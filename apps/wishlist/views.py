from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from apps.catalog.models import Product
from .models import WishlistItem
from apps.cart.views import _get_or_create_cart
from apps.cart.models import CartItem


@login_required
def wishlist_view(request):
    items = WishlistItem.objects.filter(user=request.user).select_related("product").prefetch_related("product__images")
    return render(request, "wishlist/wishlist.html", {"items": items})


@login_required
def toggle_wishlist_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    item = WishlistItem.objects.filter(user=request.user, product=product).first()

    if item:
        item.delete()
        added = False
        msg = f"'{product.name}' removed from your Wishlist."
    else:
        WishlistItem.objects.create(user=request.user, product=product)
        added = True
        msg = f"'{product.name}' saved to your Wishlist!"

    count = WishlistItem.objects.filter(user=request.user).count()

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if is_ajax:
        return JsonResponse({
            "success": True,
            "added": added,
            "message": msg,
            "wishlist_count": count,
        })

    if added:
        messages.success(request, msg)
    else:
        messages.info(request, msg)
    return redirect(request.META.get("HTTP_REFERER", "wishlist:wishlist"))


@login_required
def remove_from_wishlist_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    WishlistItem.objects.filter(user=request.user, product=product).delete()
    messages.info(request, f"'{product.name}' removed from your Wishlist.")
    return redirect("wishlist:wishlist")


@login_required
def move_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if not product.in_stock:
        messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
        return redirect("wishlist:wishlist")

    # Add to cart
    cart = _get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created and cart_item.quantity < product.stock:
        cart_item.quantity += 1
        cart_item.save()

    # Remove from wishlist
    WishlistItem.objects.filter(user=request.user, product=product).delete()

    messages.success(request, f"'{product.name}' moved to your Cart!")
    return redirect("cart:cart_detail")
