from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import robots_txt_view, sitemap_xml_view

urlpatterns = [
    # Search Engine Crawlers & Sitemaps
    path("robots.txt", robots_txt_view, name="robots_txt"),
    path("sitemap.xml", sitemap_xml_view, name="sitemap_xml"),

    # Built-in Django Admin
    path("django-admin/", admin.site.urls),

    # Custom Admin Dashboard (Plat4Sale Management Panel)
    path("dashboard/", include("apps.dashboard.urls")),

    # Public Store & Catalog
    path("", include("apps.catalog.urls")),

    # Customer Accounts
    path("accounts/", include("apps.accounts.urls")),

    # Cart
    path("cart/", include("apps.cart.urls")),

    # Wishlist
    path("wishlist/", include("apps.wishlist.urls")),

    # Orders & Checkout
    path("orders/", include("apps.orders.urls")),

    # Reviews
    path("reviews/", include("apps.reviews.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
