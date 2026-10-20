from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from apps.catalog.models import Product
from .models import Cart, CartItem
from apps.core.models import StoreSettings
from decimal import Decimal


def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart


def cart_detail_view(request):
    # Clear any lingering Buy Now session so checkout from cart includes all cart items
    request.session.pop("buy_now_data", None)
    cart = _get_or_create_cart(request)
    settings = StoreSettings.get_settings()
    free_shipping_threshold = settings.free_shipping_threshold

    amount_needed_for_free_shipping = Decimal("0.00")
    free_shipping_progress = 100
    if cart.subtotal < free_shipping_threshold and cart.subtotal > Decimal("0.00"):
        amount_needed_for_free_shipping = free_shipping_threshold - cart.subtotal
        free_shipping_progress = int((cart.subtotal / free_shipping_threshold) * 100)

    return render(request, "cart/cart_detail.html", {
        "cart": cart,
        "items": cart.items.select_related("product").all(),
        "free_shipping_threshold": free_shipping_threshold,
        "amount_needed_for_free_shipping": amount_needed_for_free_shipping,
        "free_shipping_progress": min(free_shipping_progress, 100),
    })


def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if not product.in_stock or product.stock <= 0:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": "Sorry, this product is out of stock."}, status=400)
        messages.error(request, f"Sorry, '{product.name}' is out of stock.")
        return redirect(request.META.get("HTTP_REFERER", "catalog:product_list"))

    # Extract size and color
    selected_size = request.POST.get("size", "").strip()
    selected_color = request.POST.get("color", "").strip()

    # If product has sizes available and none selected, prompt user
    if product.sizes_list and not selected_size:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": False,
                "needs_options": True,
                "redirect_url": product.get_absolute_url(),
                "message": "Please choose a size on the product page."
            }, status=400)
        messages.warning(request, "Please select an available size before adding to cart.")
        return redirect(product.get_absolute_url())

    try:
        quantity = int(request.POST.get("quantity", 1))
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1

    # Strict stock limitation check: customer quantity CANNOT exceed available stock
    if quantity > product.stock:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": False,
                "message": f"Requested quantity exceeds available stock ({product.stock} units available)."
            }, status=400)
        messages.error(request, f"Cannot order {quantity} units. Only {product.stock} units are currently in stock.")
        return redirect(product.get_absolute_url())

    # Check if this is a direct "Buy Now" action: checkout only this product, keep cart untouched
    if request.POST.get("buy_now") == "1":
        request.session["buy_now_data"] = {
            "product_id": product.id,
            "quantity": quantity,
            "selected_size": selected_size,
            "selected_color": selected_color,
        }
        return redirect(f"{reverse('orders:checkout')}?buy_now=1")

    cart = _get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        selected_size=selected_size,
        selected_color=selected_color,
        defaults={"quantity": min(quantity, product.stock)}
    )

    if not created:
        if cart_item.quantity + quantity > product.stock:
            max_add = product.stock - cart_item.quantity
            if max_add <= 0:
                msg = f"You already have all {product.stock} available units of '{product.name}' in your cart."
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": msg, "already_max": True}, status=400)
                messages.warning(request, msg)
                return redirect("cart:cart_detail")
            cart_item.quantity = product.stock
        else:
            cart_item.quantity += quantity
        cart_item.save()

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("format") == "json"
    if is_ajax:
        return JsonResponse({
            "success": True,
            "message": f"'{product.name}' added to your Cart!",
            "cart_count": cart.total_items,
            "cart_subtotal": str(cart.subtotal),
            "item_quantity": cart_item.quantity,
            "product_id": product.id,
            "in_cart": True,
        })

    messages.success(request, f"'{product.name}' added to your Cart!")
    return redirect("cart:cart_detail")


def update_cart_item_view(request, item_id):
    cart = _get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    action = request.POST.get("action")

    if action == "increase":
        if item.quantity < item.product.stock:
            item.quantity += 1
            item.save()
        else:
            messages.warning(request, f"Cannot add more. Maximum available stock is {item.product.stock} units.")
    elif action == "decrease":
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
            item = None
    else:
        try:
            qty = int(request.POST.get("quantity", 1))
            if qty > 0:
                if qty > item.product.stock:
                    messages.warning(request, f"Capped to maximum available stock ({item.product.stock} units).")
                    item.quantity = item.product.stock
                else:
                    item.quantity = qty
                item.save()
            else:
                item.delete()
                item = None
        except ValueError:
            pass

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if is_ajax:
        return JsonResponse({
            "success": True,
            "cart_count": cart.total_items,
            "cart_subtotal": str(cart.subtotal),
            "cart_total": str(cart.total_amount),
            "shipping_fee": str(cart.shipping_fee),
            "item_quantity": item.quantity if item else 0,
            "item_subtotal": str(item.subtotal) if item else "0.00",
        })

    return redirect("cart:cart_detail")


def remove_cart_item_view(request, item_id):
    cart = _get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    product_name = item.product.name
    item.delete()

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if is_ajax:
        return JsonResponse({
            "success": True,
            "message": f"'{product_name}' removed from Cart.",
            "cart_count": cart.total_items,
            "cart_subtotal": str(cart.subtotal),
            "cart_total": str(cart.total_amount),
            "shipping_fee": str(cart.shipping_fee),
        })

    messages.info(request, f"'{product_name}' was removed from your cart.")
    return redirect("cart:cart_detail")


def clear_cart_view(request):
    cart = _get_or_create_cart(request)
    cart.items.all().delete()
    messages.info(request, "Your cart is now empty.")
    return redirect("cart:cart_detail")
