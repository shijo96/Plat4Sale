from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("products/", views.product_list_view, name="product_list"),
    path("products/<slug:slug>/", views.product_detail_view, name="product_detail"),
    path("category/<slug:slug>/", views.category_detail_view, name="category_detail"),
    path("api/search-suggest/", views.search_suggest_api, name="search_suggest"),
    path("api/track-click/<int:product_id>/", views.track_product_click_api, name="track_product_click"),
]
