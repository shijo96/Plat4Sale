from django.db import models
from django.conf import settings
from apps.catalog.models import Product


class Review(models.Model):
    RATING_CHOICES = [
        (5, "★★★★★ (5/5 Excellent)"),
        (4, "★★★★☆ (4/5 Very Good)"),
        (3, "★★★☆☆ (3/5 Good)"),
        (2, "★★☆☆☆ (2/5 Fair)"),
        (1, "★☆☆☆☆ (1/5 Poor)"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    title = models.CharField(max_length=150, verbose_name="Review Headline")
    comment = models.TextField(verbose_name="Detailed Review")
    is_approved = models.BooleanField(default=True, verbose_name="Approved")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "product")
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"

    def __str__(self):
        return f"{self.rating}★ by {self.user.username} on {self.product.name}"
