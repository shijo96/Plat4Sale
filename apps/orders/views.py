import random
import string
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Order, OrderItem
from apps.cart.views import _get_or_create_cart
from apps.accounts.models import Address
from apps.core.models import StoreSettings


def _generate_order_number():
    random_digits = "".join(random.choices(string.digits, k=5))
    order_num = f"PS-{random_digits}"
    while Order.objects.filter(order_number=order_num).exists():
        random_digits = "".join(random.choices(string.digits, k=5))
        order_num = f"PS-{random_digits}"
    return order_num


@login_required
def checkout_view(request):
    cart = _get_or_create_cart(request)
    cart_items = cart.items.select_related("product").all()

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Please add items before checking out.")
        return redirect("catalog:product_list")

    # Check stock availability
    for item in cart_items:
        if item.quantity > item.product.stock:
            messages.error(
                request,
                f"Sorry, '{item.product.name}' only has {item.product.stock} items available in stock. Please adjust your cart quantity."
            )
            return redirect("cart:cart_detail")

    user_addresses = request.user.addresses.all()
    default_address = user_addresses.filter(is_default=True).first() or user_addresses.first()
    store = StoreSettings.get_settings()

    if request.method == "POST":
        address_id = request.POST.get("address_id")
        selected_address = None

        if address_id and address_id != "new":
            selected_address = user_addresses.filter(id=address_id).first()

        # If new address is supplied
        if not selected_address:
            full_name = request.POST.get("full_name", "").strip()
            phone = request.POST.get("phone", "").strip()
            line1 = request.POST.get("address_line1", "").strip()
            line2 = request.POST.get("address_line2", "").strip()
            landmark = request.POST.get("landmark", "").strip()
            city = request.POST.get("city", "").strip()
            state = request.POST.get("state", "").strip()
            pincode = request.POST.get("pincode", "").strip()

            if not (full_name and phone and line1 and city and state and pincode):
                messages.error(request, "Please fill in all required delivery address fields.")
                return render(request, "orders/checkout.html", {
                    "cart": cart,
                    "cart_items": cart_items,
                    "addresses": user_addresses,
                    "default_address": default_address,
                    "store": store,
                })

            # Optionally save to user address book
            if request.POST.get("save_address") == "1":
                selected_address = Address.objects.create(
                    user=request.user,
                    full_name=full_name,
                    phone=phone,
                    address_line1=line1,
                    address_line2=line2,
                    landmark=landmark,
                    city=city,
                    state=state,
                    pincode=pincode,
                    is_default=(not user_addresses.exists()),
                )
            else:
                selected_address = Address(
                    full_name=full_name,
                    phone=phone,
                    address_line1=line1,
                    address_line2=line2,
                    landmark=landmark,
                    city=city,
                    state=state,
                    pincode=pincode,
                )

        payment_method = request.POST.get("payment_method", Order.PAYMENT_COD)
        order_notes = request.POST.get("order_notes", "").strip()

        # Atomic transaction to guarantee order creation and stock decrements
        with transaction.atomic():
            order_number = _generate_order_number()
            order = Order.objects.create(
                order_number=order_number,
                user=request.user,
                customer_name=selected_address.full_name,
                customer_phone=selected_address.phone,
                customer_email=request.user.email,
                shipping_address_line1=selected_address.address_line1,
                shipping_address_line2=selected_address.address_line2,
                shipping_landmark=selected_address.landmark or "",
                shipping_city=selected_address.city,
                shipping_state=selected_address.state,
                shipping_pincode=selected_address.pincode,
                payment_method=payment_method,
                status=Order.STATUS_PENDING,
                subtotal=cart.subtotal,
                shipping_fee=cart.shipping_fee,
                total_amount=cart.total_amount,
                order_notes=order_notes,
            )

            # Create OrderItems and decrement stock
            for item in cart_items:
                product = item.product
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_sku=product.sku,
                    unit_price=product.current_price,
                    quantity=item.quantity,
                    subtotal=item.subtotal,
                )
                product.stock = max(0, product.stock - item.quantity)
                product.save()

            # Clear cart
            cart.items.all().delete()

        messages.success(request, f"Order #{order.order_number} placed successfully!")
        return redirect("orders:order_confirmation", order_number=order.order_number)

    return render(request, "orders/checkout.html", {
        "cart": cart,
        "cart_items": cart_items,
        "addresses": user_addresses,
        "default_address": default_address,
        "store": store,
    })


@login_required
def order_confirmation_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    store = StoreSettings.get_settings()
    whatsapp_url = order.get_whatsapp_url(business_phone=store.whatsapp_number)

    return render(request, "orders/order_confirmation.html", {
        "order": order,
        "items": order.items.all(),
        "store": store,
        "whatsapp_url": whatsapp_url,
    })


@login_required
def my_orders_view(request):
    orders = request.user.orders.prefetch_related("items").all()
    return render(request, "orders/my_orders.html", {"orders": orders})


@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    store = StoreSettings.get_settings()
    whatsapp_url = order.get_whatsapp_url(business_phone=store.whatsapp_number)

    return render(request, "orders/order_detail.html", {
        "order": order,
        "items": order.items.all(),
        "store": store,
        "whatsapp_url": whatsapp_url,
    })


@login_required
def cancel_order_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if not order.can_cancel:
        messages.error(request, f"Order #{order.order_number} cannot be cancelled as it has already reached '{order.get_status_display()}' stage.")
        return redirect("orders:order_detail", order_number=order.order_number)

    with transaction.atomic():
        order.status = Order.STATUS_CANCELLED
        order.save()

        # Restore product stock
        for item in order.items.all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save()

    messages.info(request, f"Order #{order.order_number} has been cancelled.")
    return redirect("orders:order_detail", order_number=order.order_number)
