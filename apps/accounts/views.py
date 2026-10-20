from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.urls import reverse
from .models import User, Address
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, AddressForm
from apps.cart.models import Cart, CartItem


def _merge_guest_cart(request, user):
    """Merges any items in a guest session cart into the user's permanent cart upon login."""
    session_key = request.session.session_key
    if not session_key:
        return

    guest_cart = Cart.objects.filter(session_key=session_key).first()
    if not guest_cart:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)

    for item in guest_cart.items.all():
        existing_item = user_cart.items.filter(product=item.product).first()
        if existing_item:
            existing_item.quantity += item.quantity
            existing_item.save()
        else:
            item.cart = user_cart
            item.save()

    guest_cart.delete()


def register_view(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")

    next_url = request.GET.get("next") or request.POST.get("next") or "catalog:home"

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            _merge_guest_cart(request, user)
            messages.success(request, f"Welcome to Plat4Sale, {user.first_name or user.username}! Your account has been created.")
            return redirect(next_url)
    else:
        form = UserRegistrationForm()

    return render(request, "accounts/register.html", {"form": form, "next": next_url})


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("dashboard:home")
        return redirect("catalog:home")

    next_url = request.GET.get("next") or request.POST.get("next") or ""

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.user
            login(request, user)
            request.session.modified = True
            _merge_guest_cart(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")

            # Smart redirection: if next is given, follow it; if admin/staff, go to dashboard
            if next_url and next_url not in ["catalog:home", "/"]:
                return redirect(next_url)
            if user.is_staff or user.is_superuser:
                return redirect("dashboard:home")
            return redirect("catalog:home")
    else:
        form = UserLoginForm()

    return render(request, "accounts/login.html", {"form": form, "next": next_url})


def logout_view(request):
    # Completely flush and clear session data
    request.session.flush()
    logout(request)
    messages.success(request, "You have been logged out securely. Your session has been cleared.")
    return redirect("catalog:home")


@login_required
def profile_view(request):
    user = request.user
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been updated successfully.")
            return redirect("accounts:profile")
    else:
        form = UserProfileForm(instance=user)

    recent_orders = user.orders.all()[:5]
    addresses = user.addresses.all()

    return render(request, "customer/profile.html", {
        "form": form,
        "recent_orders": recent_orders,
        "addresses": addresses,
    })


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, "Your password was successfully updated!")
            return redirect("accounts:profile")
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "customer/change_password.html", {"form": form})


@login_required
def address_list_view(request):
    addresses = request.user.addresses.all()
    return render(request, "customer/addresses.html", {"addresses": addresses})


@login_required
def address_add_view(request):
    next_url = request.GET.get("next") or "accounts:address_list"

    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            # If this is the user's only address, make it default automatically
            if not request.user.addresses.exists():
                address.is_default = True
            address.save()
            messages.success(request, "New address added successfully.")
            return redirect(next_url)
    else:
        form = AddressForm()

    return render(request, "customer/address_form.html", {
        "form": form,
        "title": "Add New Delivery Address",
        "next": next_url,
    })


@login_required
def address_edit_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    next_url = request.GET.get("next") or "accounts:address_list"

    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully.")
            return redirect(next_url)
    else:
        form = AddressForm(instance=address)

    return render(request, "customer/address_form.html", {
        "form": form,
        "title": "Edit Delivery Address",
        "next": next_url,
    })


@login_required
def address_delete_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        address.delete()
        messages.success(request, "Address deleted successfully.")
    return redirect("accounts:address_list")


@login_required
def address_set_default_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, f"'{address.full_name}' is now set as your default address.")
    return redirect("accounts:address_list")
