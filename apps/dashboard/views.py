from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from .decorators import staff_required
from .forms import ProductAdminForm, CategoryAdminForm, BannerAdminForm, StoreSettingsForm
from apps.catalog.models import Product, ProductImage, Category, Banner
from apps.orders.models import Order, OrderItem
from apps.accounts.models import User
from apps.reviews.models import Review
from apps.core.models import StoreSettings


@staff_required
def dashboard_home(request):
    # Aggregated metrics
    total_sales = Order.objects.exclude(status=Order.STATUS_CANCELLED).aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status=Order.STATUS_PENDING).count()
    delivered_orders = Order.objects.filter(status=Order.STATUS_DELIVERED).count()

    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(stock__lte=5, is_active=True).count()
    total_customers = User.objects.filter(is_staff=False).count()
    pending_reviews = Review.objects.filter(is_approved=False).count()

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

            # Handle primary photo upload
            primary_img = request.FILES.get("primary_image")
            if primary_img:
                ProductImage.objects.create(product=product, image=primary_img, is_primary=True, sort_order=0)

            # Additional photos
            img2 = request.FILES.get("additional_image_1")
            if img2:
                ProductImage.objects.create(product=product, image=img2, is_primary=False, sort_order=1)
            img3 = request.FILES.get("additional_image_2")
            if img3:
                ProductImage.objects.create(product=product, image=img3, is_primary=False, sort_order=2)

            messages.success(request, f"Product '{product.name}' was created successfully!")
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

            primary_img = request.FILES.get("primary_image")
            if primary_img:
                ProductImage.objects.filter(product=product, is_primary=True).delete()
                ProductImage.objects.create(product=product, image=primary_img, is_primary=True, sort_order=0)

            img2 = request.FILES.get("additional_image_1")
            if img2:
                ProductImage.objects.create(product=product, image=img2, is_primary=False, sort_order=1)
            img3 = request.FILES.get("additional_image_2")
            if img3:
                ProductImage.objects.create(product=product, image=img3, is_primary=False, sort_order=2)

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
        form = StoreSettingsForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, "Store and WhatsApp settings updated successfully.")
            return redirect("dashboard:settings")
    else:
        form = StoreSettingsForm(instance=store)

    return render(request, "dashboard/settings.html", {"form": form, "store": store})
