from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    # Dashboard Home
    path("", views.dashboard_home, name="home"),

    # Products
    path("products/", views.product_list_view, name="product_list"),
    path("products/add/", views.product_add_view, name="product_add"),
    path("products/<int:pk>/edit/", views.product_edit_view, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete_view, name="product_delete"),

    # Categories
    path("categories/", views.category_list_view, name="category_list"),
    path("categories/add/", views.category_add_view, name="category_add"),
    path("categories/<int:pk>/edit/", views.category_edit_view, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete_view, name="category_delete"),

    # Orders
    path("orders/", views.order_list_view, name="order_list"),
    path("orders/<int:pk>/", views.order_detail_view, name="order_detail"),
    path("orders/<int:pk>/invoice/", views.order_invoice_view, name="order_invoice"),

    # Customers
    path("customers/", views.customer_list_view, name="customer_list"),

    # Reviews
    path("reviews/", views.review_list_view, name="review_list"),

    # Banners
    path("banners/", views.banner_list_view, name="banner_list"),
    path("banners/add/", views.banner_add_view, name="banner_add"),
    path("banners/<int:pk>/edit/", views.banner_edit_view, name="banner_edit"),
    path("banners/<int:pk>/delete/", views.banner_delete_view, name="banner_delete"),

    # Settings
    path("settings/", views.settings_view, name="settings"),
]
