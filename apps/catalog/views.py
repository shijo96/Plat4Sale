from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, F
from django.db import models
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from .models import Category, Product, Banner, ProductClick
from apps.reviews.models import Review
from apps.core.middleware import get_client_ip


def home_view(request):
    hero_banners = Banner.objects.filter(is_active=True, placement="hero").order_by("sort_order", "-created_at")
    promo_banners = Banner.objects.filter(is_active=True, placement="promo_grid").order_by("sort_order")[:4]
    strip_banner = Banner.objects.filter(is_active=True, placement="promo_strip").first()

    categories = Category.objects.filter(is_active=True, is_featured=True).order_by("sort_order")[:8]
    featured_products = Product.objects.filter(is_active=True, is_featured=True).select_related("category").prefetch_related("images")[:8]
    bestsellers = Product.objects.filter(is_active=True, is_bestseller=True).select_related("category").prefetch_related("images")[:8]
    new_arrivals = Product.objects.filter(is_active=True, is_new_arrival=True).select_related("category").prefetch_related("images")[:8]

    # Deals: products with active discount
    deals = Product.objects.filter(is_active=True, sale_price__isnull=False).select_related("category").prefetch_related("images")[:8]

    # Wishlist IDs for user
    user_wishlist_ids = set()
    if request.user.is_authenticated:
        user_wishlist_ids = set(request.user.wishlist_items.values_list("product_id", flat=True))

    return render(request, "store/home.html", {
        "hero_banners": hero_banners,
        "promo_banners": promo_banners,
        "strip_banner": strip_banner,
        "featured_categories": categories,
        "featured_products": featured_products,
        "bestsellers": bestsellers,
        "new_arrivals": new_arrivals,
        "deals": deals,
        "user_wishlist_ids": user_wishlist_ids,
    })


def product_list_view(request):
    products = Product.objects.filter(is_active=True).select_related("category").prefetch_related("images")
    categories = Category.objects.filter(is_active=True)

    # Search filter
    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(sku__icontains=q) |
            Q(category__name__icontains=q)
        )

    # Category filter
    category_slug = request.GET.get("category", "").strip()
    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(slug=category_slug).first()
        if selected_category:
            products = products.filter(category=selected_category)

    # Price filters
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # In stock filter
    if request.GET.get("in_stock") == "1":
        products = products.filter(stock__gt=0)

    # Sorting
    sort = request.GET.get("sort", "featured")
    if sort == "price_low":
        products = products.order_by("sale_price", "price")
    elif sort == "price_high":
        products = products.order_by("-sale_price", "-price")
    elif sort == "newest":
        products = products.order_by("-created_at")
    elif sort == "bestseller":
        products = products.order_by("-is_bestseller", "-created_at")
    else:
        products = products.order_by("-is_featured", "-created_at")

    # Pagination: 12 products per page
    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    user_wishlist_ids = set()
    if request.user.is_authenticated:
        user_wishlist_ids = set(request.user.wishlist_items.values_list("product_id", flat=True))

    return render(request, "store/product_list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "selected_category": selected_category,
        "q": q,
        "sort": sort,
        "min_price": min_price or "",
        "max_price": max_price or "",
        "in_stock": request.GET.get("in_stock", ""),
        "total_count": paginator.count,
        "user_wishlist_ids": user_wishlist_ids,
    })


def category_detail_view(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True).select_related("category").prefetch_related("images")

    sort = request.GET.get("sort", "featured")
    if sort == "price_low":
        products = products.order_by("sale_price", "price")
    elif sort == "price_high":
        products = products.order_by("-sale_price", "-price")
    elif sort == "newest":
        products = products.order_by("-created_at")
    else:
        products = products.order_by("-is_featured", "-created_at")

    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    user_wishlist_ids = set()
    if request.user.is_authenticated:
        user_wishlist_ids = set(request.user.wishlist_items.values_list("product_id", flat=True))

    return render(request, "store/category_detail.html", {
        "category": category,
        "page_obj": page_obj,
        "sort": sort,
        "total_count": paginator.count,
        "user_wishlist_ids": user_wishlist_ids,
    })


def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    images = product.images.all()
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id)[:4]

    reviews = product.reviews.filter(is_approved=True).select_related("user")
    reviews_count = reviews.count()

    # Calculate rating breakdown
    rating_breakdown = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    if reviews_count > 0:
        for r in reviews:
            rating_breakdown[r.rating] = rating_breakdown.get(r.rating, 0) + 1
        for star in rating_breakdown:
            rating_breakdown[star] = int((rating_breakdown[star] / reviews_count) * 100)

    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = product.reviews.filter(user=request.user).exists()

    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = request.user.wishlist_items.filter(product=product).exists()

    return render(request, "store/product_detail.html", {
        "product": product,
        "images": images,
        "related_products": related_products,
        "reviews": reviews,
        "reviews_count": reviews_count,
        "rating_breakdown": rating_breakdown,
        "user_has_reviewed": user_has_reviewed,
        "is_wishlisted": is_wishlisted,
    })


def search_suggest_api(request):
    """Instant JSON search suggest API for live dropdown search"""
    q = request.GET.get("q", "").strip()
    if not q or len(q) < 2:
        return JsonResponse({"results": []})

    products = Product.objects.filter(
        Q(name__icontains=q) | Q(category__name__icontains=q),
        is_active=True
    )[:6]

    results = []
    for p in products:
        img_url = p.primary_image.image.url if p.primary_image else "/static/images/logo.jpg"
        results.append({
            "name": p.name,
            "url": p.get_absolute_url(),
            "price": f"₹{p.current_price}",
            "original_price": f"₹{p.price}" if p.sale_price else "",
            "category": p.category.name,
            "image": img_url,
        })
    return JsonResponse({"results": results})


@csrf_exempt
def track_product_click_api(request, product_id):
    """
    Records a click on a product card or link from anywhere in the store.
    Increments views_count and saves a timestamped ProductClick record.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if request.user.is_authenticated and request.user.is_staff:
        return JsonResponse({"status": "ignored_staff", "product_id": product.id, "views": product.views_count})

    session_key = request.session.session_key or "anonymous"
    ip = get_client_ip(request)
    user = request.user if request.user.is_authenticated else None
    now = timezone.now()

    # Deduplicate rapid clicks within 30 seconds
    recent_click = ProductClick.objects.filter(
        product=product,
        session_key=session_key,
        timestamp__gte=now - timedelta(seconds=30),
    ).exists()

    if not recent_click:
        ProductClick.objects.create(
            product=product,
            session_key=session_key,
            user=user,
            ip_address=ip,
        )
        Product.objects.filter(id=product.id).update(views_count=models.F("views_count") + 1)

    return JsonResponse({"status": "success", "product_id": product.id, "views": product.views_count + 1})
