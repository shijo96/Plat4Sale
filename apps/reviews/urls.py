from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("add/<slug:slug>/", views.add_review_view, name="add_review"),
]
