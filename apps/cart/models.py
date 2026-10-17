from django.db import models
from django.conf import settings
from apps.catalog.models import Product
from decimal import Decimal


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="carts")
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.username}"
        return f"Guest Cart ({self.session_key})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        total = Decimal("0.00")
        for item in self.items.select_related("product").all():
            total += item.subtotal
        return total

    @property
    def shipping_fee(self):
        # Free delivery over ₹499
        if self.subtotal >= Decimal("499.00") or self.subtotal == Decimal("0.00"):
            return Decimal("0.00")
        return Decimal("49.00")

    @property
    def total_amount(self):
        return self.subtotal + self.shipping_fee


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def unit_price(self):
        return self.product.current_price

    @property
    def subtotal(self):
        return self.product.current_price * self.quantity
