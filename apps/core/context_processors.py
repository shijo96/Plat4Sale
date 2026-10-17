from datetime import datetime
from apps.core.models import StoreSettings
from apps.catalog.models import Category
from apps.cart.models import Cart
from apps.wishlist.models import WishlistItem


def store_context(request):
    try:
        settings = StoreSettings.get_settings()
    except Exception:
        settings = None

    try:
        categories = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    except Exception:
        categories = []

    cart_count = 0
    cart_subtotal = 0
    wishlist_count = 0

    try:
        # Determine cart
        if request.user.is_authenticated:
            user_cart = Cart.objects.filter(user=request.user).first()
            if user_cart:
                cart_count = user_cart.total_items
                cart_subtotal = user_cart.subtotal
            wishlist_count = WishlistItem.objects.filter(user=request.user).count()
        else:
            session_key = request.session.session_key
            if session_key:
                guest_cart = Cart.objects.filter(session_key=session_key).first()
                if guest_cart:
                    cart_count = guest_cart.total_items
                    cart_subtotal = guest_cart.subtotal
    except Exception:
        pass

    return {
        "store": settings,
        "nav_categories": categories,
        "cart_count": cart_count,
        "cart_subtotal": cart_subtotal,
        "wishlist_count": wishlist_count,
        "current_year": datetime.now().year,
    }
