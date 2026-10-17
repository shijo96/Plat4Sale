from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.my_orders_view, name="my_orders"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("confirmation/<str:order_number>/", views.order_confirmation_view, name="order_confirmation"),
    path("<str:order_number>/", views.order_detail_view, name="order_detail"),
    path("<str:order_number>/cancel/", views.cancel_order_view, name="cancel_order"),
]
