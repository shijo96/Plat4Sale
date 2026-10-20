import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.core.paginator import Paginator
from .decorators import staff_required
from .forms import ProductAdminForm, CategoryAdminForm, BannerAdminForm, StoreSettingsForm
from apps.catalog.models import Product, ProductImage, Category, Banner, ProductClick
from apps.orders.models import Order, OrderItem
from apps.orders.services import notify_low_stock
from apps.accounts.models import User
from apps.reviews.models import Review
from apps.core.models import StoreSettings, SiteVisit


@staff_required
def dashboard_home(request):
    now = timezone.now()

    # Aggregated financial and order metrics
    total_sales = Order.objects.exclude(status=Order.STATUS_CANCELLED).aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status=Order.STATUS_PENDING).count()
    delivered_orders = Order.objects.filter(status=Order.STATUS_DELIVERED).count()

    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(stock__lte=5, is_active=True).count()
    total_customers = User.objects.filter(is_staff=False).count()
    pending_reviews = Review.objects.filter(is_approved=False).count()

    # Website Traffic & Live Customer presence
    live_visitors = SiteVisit.objects.filter(last_activity__gte=now - timedelta(minutes=5)).values("session_key").distinct().count()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_pageviews = SiteVisit.objects.filter(timestamp__gte=today_start).count()
    today_visitors = SiteVisit.objects.filter(timestamp__gte=today_start).values("session_key").distinct().count()

    # Quick Product Highlights
    top_clicked_product = Product.objects.filter(is_active=True).order_by("-views_count").first()
    top_ordered_product = Product.objects.annotate(
        total_ordered_qty=Sum(
            "order_items__quantity",
            filter=Q(
                order_items__order__status__in=[
                    Order.STATUS_PENDING, Order.STATUS_CONFIRMED,
                    Order.STATUS_PROCESSING, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED
                ]
            )
        )
    ).filter(total_ordered_qty__gt=0).order_by("-total_ordered_qty").first()

    recent_orders = Order.objects.select_related("user").prefetch_related("items").all()[:10]
    recent_products = Product.objects.select_related("category").all()[:6]

    return render(request, "dashboard/home.html", {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        "total_products": total_products,
        "low_stock_products": low_stock_products,
        "total_customers": total_customers,
        "pending_reviews": pending_reviews,
        "live_visitors": live_visitors,
        "today_pageviews": today_pageviews,
        "today_visitors": today_visitors,
        "top_clicked_product": top_clicked_product,
        "top_ordered_product": top_ordered_product,
        "recent_orders": recent_orders,
        "recent_products": recent_products,
    })


# ---------------- PRODUCT MANAGEMENT ---------------- #

@staff_required
def product_list_view(request):
    products = Product.objects.select_related("category").prefetch_related("images").all()

    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q))

    category_id = request.GET.get("category")
    if category_id:
        products = products.filter(category_id=category_id)

    stock_status = request.GET.get("stock")
    if stock_status == "out":
        products = products.filter(stock=0)
    elif stock_status == "low":
        products = products.filter(stock__gt=0, stock__lte=5)
    elif stock_status == "in":
        products = products.filter(stock__gt=5)

    paginator = Paginator(products, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    categories = Category.objects.all()

    return render(request, "dashboard/products/list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "q": q,
        "selected_category": category_id or "",
        "stock_status": stock_status or "",
    })


@staff_required
def product_add_view(request):
    if request.method == "POST":
        form = ProductAdminForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()

            # Slot 1: Compulsory Primary Image
            primary_img = request.FILES.get("primary_image")
            if primary_img:
                ProductImage.objects.create(
                    product=product,
                    image=primary_img,
                    is_primary=True,
                    sort_order=0,
                    alt_text=f"{product.name} Main Photo"
                )

            # Slots 2 to 10: Optional Images or Videos
            for slot_num in range(2, 11):
                media_file = request.FILES.get(f"media_{slot_num}")
                if media_file:
                    ProductImage.objects.create(
                        product=product,
                        image=media_file,
                        is_primary=False,
                        sort_order=slot_num - 1,
                        alt_text=f"{product.name} Media {slot_num}"
                    )

            # Low stock notification if initialized with <= 5 units
            if 0 < product.stock <= 5:
                notify_low_stock(product)

            messages.success(request, f"Product '{product.name}' was created successfully with media gallery!")
            return redirect("dashboard:product_list")
    else:
        form = ProductAdminForm()

    return render(request, "dashboard/products/form.html", {
        "form": form,
        "title": "Add New Product",
    })


@staff_required
def product_edit_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductAdminForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()

            # Slot 1: Primary Image (replace if uploaded)
            primary_img = request.FILES.get("primary_image")
            if primary_img:
                ProductImage.objects.filter(product=product, is_primary=True).delete()
                ProductImage.objects.create(
                    product=product,
                    image=primary_img,
                    is_primary=True,
                    sort_order=0,
                    alt_text=f"{product.name} Main Photo"
                )

            # Slots 2 to 10: Optional Images or Videos
            for slot_num in range(2, 11):
                media_file = request.FILES.get(f"media_{slot_num}")
                if media_file:
                    # Enforce max 10 total media items
                    if product.images.count() < 10:
                        ProductImage.objects.create(
                            product=product,
                            image=media_file,
                            is_primary=False,
                            sort_order=slot_num - 1,
                            alt_text=f"{product.name} Media {slot_num}"
                        )

            # Check if updated stock is low
            if 0 < product.stock <= 5:
                notify_low_stock(product)

            messages.success(request, f"Product '{product.name}' was updated successfully!")
            return redirect("dashboard:product_list")
    else:
        form = ProductAdminForm(instance=product)

    return render(request, "dashboard/products/form.html", {
        "form": form,
        "product": product,
        "title": f"Edit Product: {product.name}",
    })


@staff_required
def product_media_delete_view(request, pk, media_id):
    product = get_object_or_404(Product, pk=pk)
    media_item = get_object_or_404(ProductImage, id=media_id, product=product)

    if request.method == "POST":
        if media_item.is_primary:
            messages.warning(request, "Cannot delete primary image. Please upload a new primary image first.")
        else:
            media_item.delete()
            messages.success(request, "Media item removed from gallery.")

    return redirect("dashboard:product_edit", pk=product.id)


@staff_required
def product_delete_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' was deleted.")
    return redirect("dashboard:product_list")


# ---------------- CATEGORY MANAGEMENT ---------------- #

@staff_required
def category_list_view(request):
    categories = Category.objects.annotate(product_count=Count("products")).order_by("sort_order", "name")
    return render(request, "dashboard/categories/list.html", {"categories": categories})


@staff_required
def category_add_view(request):
    if request.method == "POST":
        form = CategoryAdminForm(request.POST, request.FILES)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Category '{cat.name}' created successfully.")
            return redirect("dashboard:category_list")
    else:
        form = CategoryAdminForm()

    return render(request, "dashboard/categories/form.html", {"form": form, "title": "Add New Category"})


@staff_required
def category_edit_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryAdminForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"Category '{category.name}' updated successfully.")
            return redirect("dashboard:category_list")
    else:
        form = CategoryAdminForm(instance=category)

    return render(request, "dashboard/categories/form.html", {
        "form": form,
        "category": category,
        "title": f"Edit Category: {category.name}",
    })


@staff_required
def category_delete_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        name = category.name
        category.delete()
        messages.success(request, f"Category '{name}' deleted.")
    return redirect("dashboard:category_list")


# ---------------- ORDER MANAGEMENT ---------------- #

@staff_required
def order_list_view(request):
    orders = Order.objects.select_related("user").prefetch_related("items").all()

    q = request.GET.get("q", "").strip()
    if q:
        orders = orders.filter(
            Q(order_number__icontains=q) |
            Q(customer_name__icontains=q) |
            Q(customer_phone__icontains=q)
        )

    status = request.GET.get("status")
    if status:
        orders = orders.filter(status=status)

    payment_status = request.GET.get("payment_status")
    if payment_status:
        orders = orders.filter(payment_status=payment_status)

    paginator = Paginator(orders, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "dashboard/orders/list.html", {
        "page_obj": page_obj,
        "q": q,
        "selected_status": status or "",
        "payment_status": payment_status or "",
        "status_choices": Order.STATUS_CHOICES,
    })


@staff_required
def order_detail_view(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=pk)
    store = StoreSettings.get_settings()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_status":
            new_status = request.POST.get("status")
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                order.save()
                messages.success(request, f"Order status updated to '{order.get_status_display()}'.")
        elif action == "update_payment":
            new_payment_status = request.POST.get("payment_status")
            if new_payment_status in dict(Order.PAYMENT_STATUS_CHOICES):
                order.payment_status = new_payment_status
                order.save()
                messages.success(request, f"Payment status changed to '{order.get_payment_status_display()}'.")
        return redirect("dashboard:order_detail", pk=order.pk)

    whatsapp_url = order.get_whatsapp_url(business_phone=store.whatsapp_number)

    return render(request, "dashboard/orders/detail.html", {
        "order": order,
        "items": order.items.all(),
        "store": store,
        "whatsapp_url": whatsapp_url,
        "status_choices": Order.STATUS_CHOICES,
        "payment_status_choices": Order.PAYMENT_STATUS_CHOICES,
    })


@staff_required
def order_invoice_view(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=pk)
    store = StoreSettings.get_settings()
    return render(request, "dashboard/orders/invoice.html", {
        "order": order,
        "items": order.items.all(),
        "store": store,
    })


# ---------------- CUSTOMERS ---------------- #

@staff_required
def customer_list_view(request):
    customers = User.objects.filter(is_staff=False).annotate(
        order_count=Count("orders"),
        total_spent=Sum("orders__total_amount")
    ).order_by("-date_joined")

    q = request.GET.get("q", "").strip()
    if q:
        customers = customers.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(phone__icontains=q)
        )

    paginator = Paginator(customers, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "dashboard/customers/list.html", {
        "page_obj": page_obj,
        "q": q,
    })


# ---------------- REVIEWS MODERATION ---------------- #

@staff_required
def review_list_view(request):
    reviews = Review.objects.select_related("user", "product").order_by("-created_at")

    if request.method == "POST":
        action = request.POST.get("action")
        review_id = request.POST.get("review_id")
        review = get_object_or_404(Review, id=review_id)

        if action == "approve":
            review.is_approved = True
            review.save()
            messages.success(request, f"Review approved.")
        elif action == "reject":
            review.is_approved = False
            review.save()
            messages.info(request, f"Review hidden.")
        elif action == "delete":
            review.delete()
            messages.success(request, f"Review deleted.")
        return redirect("dashboard:review_list")

    paginator = Paginator(reviews, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "dashboard/reviews/list.html", {"page_obj": page_obj})


# ---------------- BANNERS MANAGEMENT ---------------- #

@staff_required
def banner_list_view(request):
    banners = Banner.objects.order_by("placement", "sort_order")
    return render(request, "dashboard/banners/list.html", {"banners": banners})


@staff_required
def banner_add_view(request):
    if request.method == "POST":
        form = BannerAdminForm(request.POST, request.FILES)
        if form.is_valid():
            banner = form.save()
            messages.success(request, f"Banner '{banner.title}' created.")
            return redirect("dashboard:banner_list")
    else:
        form = BannerAdminForm()
    return render(request, "dashboard/banners/form.html", {"form": form, "title": "Create Promotional Banner"})


@staff_required
def banner_edit_view(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    if request.method == "POST":
        form = BannerAdminForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, f"Banner '{banner.title}' updated.")
            return redirect("dashboard:banner_list")
    else:
        form = BannerAdminForm(instance=banner)
    return render(request, "dashboard/banners/form.html", {"form": form, "banner": banner, "title": f"Edit Banner: {banner.title}"})


@staff_required
def banner_delete_view(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    if request.method == "POST":
        banner.delete()
        messages.success(request, "Banner removed.")
    return redirect("dashboard:banner_list")


# ---------------- STORE SETTINGS ---------------- #

@staff_required
def settings_view(request):
    store = StoreSettings.get_settings()
    if request.method == "POST":
        form = StoreSettingsForm(request.POST, request.FILES, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, "Store settings, WhatsApp configuration, and SEO metadata updated successfully.")
            return redirect("dashboard:settings")
    else:
        form = StoreSettingsForm(instance=store)

    return render(request, "dashboard/settings.html", {"form": form, "store": store})


# ---------------- WEBSITE TRAFFIC & PRODUCT PERFORMANCE ANALYTICS ---------------- #

@staff_required
def analytics_view(request):
    period = request.GET.get("period", "month")
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    start_date_input = request.GET.get("start_date", "").strip()
    end_date_input = request.GET.get("end_date", "").strip()

    if period == "day":
        start_dt = today_start
        end_dt = now
        period_title = "Today"
    elif period == "week":
        start_dt = now - timedelta(days=7)
        end_dt = now
        period_title = "Past 7 Days"
    elif period == "year":
        start_dt = now - timedelta(days=365)
        end_dt = now
        period_title = "Past 365 Days"
    elif period == "custom" and start_date_input and end_date_input:
        try:
            s_d = datetime.strptime(start_date_input, "%Y-%m-%d")
            e_d = datetime.strptime(end_date_input, "%Y-%m-%d")
            start_dt = s_d.replace(hour=0, minute=0, second=0, tzinfo=timezone.get_current_timezone())
            end_dt = e_d.replace(hour=23, minute=59, second=59, tzinfo=timezone.get_current_timezone())
            period_title = f"{start_date_input} to {end_date_input}"
        except Exception:
            start_dt = now - timedelta(days=30)
            end_dt = now
            period_title = "Past 30 Days"
            period = "month"
    else:
        period = "month"
        start_dt = now - timedelta(days=30)
        end_dt = now
        period_title = "Past 30 Days"

    # 1. Live Active Visitors (active in last 5 minutes)
    live_visitors = SiteVisit.objects.filter(last_activity__gte=now - timedelta(minutes=5)).values("session_key").distinct().count()

    # 2. Total Pageviews & Unique Visitors in timeframe
    total_pageviews = SiteVisit.objects.filter(timestamp__range=(start_dt, end_dt)).count()
    unique_visitors = SiteVisit.objects.filter(timestamp__range=(start_dt, end_dt)).values("session_key").distinct().count()
    total_clicks = ProductClick.objects.filter(timestamp__range=(start_dt, end_dt)).count()
    total_orders = Order.objects.filter(created_at__range=(start_dt, end_dt)).exclude(status=Order.STATUS_CANCELLED).count()

    # 3. Daily Traffic Timeline for Chart.js
    daily_records = (
        SiteVisit.objects.filter(timestamp__range=(start_dt, end_dt))
        .annotate(d=TruncDate("timestamp"))
        .values("d")
        .annotate(
            pv=Count("id"),
            uv=Count("session_key", distinct=True)
        )
        .order_by("d")
    )
    chart_dates = []
    chart_pv = []
    chart_uv = []
    for rec in daily_records:
        if rec["d"]:
            chart_dates.append(rec["d"].strftime("%b %d"))
            chart_pv.append(rec["pv"])
            chart_uv.append(rec["uv"])

    if not chart_dates:
        chart_dates = [now.strftime("%b %d")]
        chart_pv = [total_pageviews]
        chart_uv = [unique_visitors]

    # 4. Top Clicked / Most Viewed Products Table (Ranked by highest clicks first)
    top_clicked_qs = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images")
        .annotate(
            period_clicks=Count("clicks", filter=Q(clicks__timestamp__range=(start_dt, end_dt))),
            period_orders=Count(
                "order_items",
                filter=Q(
                    order_items__order__created_at__range=(start_dt, end_dt),
                    order_items__order__status__in=[
                        Order.STATUS_PENDING, Order.STATUS_CONFIRMED,
                        Order.STATUS_PROCESSING, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED
                    ]
                )
            )
        )
        .order_by("-period_clicks", "-views_count")[:25]
    )

    top_clicked_list = []
    for p in top_clicked_qs:
        clicks_val = p.period_clicks
        orders_val = p.period_orders
        conv_rate = round((orders_val / clicks_val * 100), 1) if clicks_val > 0 else 0.0
        top_clicked_list.append({
            "product": p,
            "period_clicks": clicks_val,
            "total_views": p.views_count,
            "orders_count": orders_val,
            "conversion_rate": conv_rate,
        })

    # 5. Top Selling / Most Ordered Products Table (Ranked by highest quantity ordered in selected period)
    top_ordered_qs = (
        Product.objects.select_related("category").prefetch_related("images")
        .annotate(
            ordered_units=Sum(
                "order_items__quantity",
                filter=Q(
                    order_items__order__created_at__range=(start_dt, end_dt),
                    order_items__order__status__in=[
                        Order.STATUS_PENDING, Order.STATUS_CONFIRMED,
                        Order.STATUS_PROCESSING, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED
                    ]
                )
            ),
            order_count=Count(
                "order_items__order",
                distinct=True,
                filter=Q(
                    order_items__order__created_at__range=(start_dt, end_dt),
                    order_items__order__status__in=[
                        Order.STATUS_PENDING, Order.STATUS_CONFIRMED,
                        Order.STATUS_PROCESSING, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED
                    ]
                )
            ),
            revenue=Sum(
                models.F("order_items__quantity") * models.F("order_items__unit_price"),
                filter=Q(
                    order_items__order__created_at__range=(start_dt, end_dt),
                    order_items__order__status__in=[
                        Order.STATUS_PENDING, Order.STATUS_CONFIRMED,
                        Order.STATUS_PROCESSING, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED
                    ]
                )
            )
        )
        .filter(ordered_units__gt=0)
        .order_by("-ordered_units", "-order_count")[:25]
    )

    return render(request, "dashboard/analytics.html", {
        "period": period,
        "period_title": period_title,
        "start_date": start_date_input,
        "end_date": end_date_input,
        "live_visitors": live_visitors,
        "total_pageviews": total_pageviews,
        "unique_visitors": unique_visitors,
        "total_clicks": total_clicks,
        "total_orders": total_orders,
        "chart_dates_json": json.dumps(chart_dates),
        "chart_pv_json": json.dumps(chart_pv),
        "chart_uv_json": json.dumps(chart_uv),
        "top_clicked_list": top_clicked_list,
        "top_ordered_products": top_ordered_qs,
    })


@staff_required
def api_live_visitors(request):
    now = timezone.now()
    count = SiteVisit.objects.filter(last_activity__gte=now - timedelta(minutes=5)).values("session_key").distinct().count()
    return JsonResponse({
        "live_visitors": count,
        "timestamp": now.strftime("%H:%M:%S")
    })

