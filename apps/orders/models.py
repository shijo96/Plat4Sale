import urllib.parse
from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.catalog.models import Product


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    PAYMENT_WHATSAPP = "whatsapp"
    PAYMENT_COD = "cod"
    PAYMENT_UPI = "upi"
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_WHATSAPP, "Order via WhatsApp"),
        (PAYMENT_COD, "Cash on Delivery (COD)"),
        (PAYMENT_UPI, "Pay via UPI / QR Code"),
    ]

    PAYMENT_STATUS_UNPAID = "unpaid"
    PAYMENT_STATUS_PAID = "paid"
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_UNPAID, "Unpaid"),
        (PAYMENT_STATUS_PAID, "Paid"),
    ]

    order_number = models.CharField(max_length=32, unique=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")

    # Customer snapshot
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(blank=True)

    # Address snapshot
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_landmark = models.CharField(max_length=150, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_pincode = models.CharField(max_length=10)

    # Order details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_WHATSAPP)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_UNPAID)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    order_notes = models.TextField(blank=True)
    whatsapp_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order #{self.order_number} ({self.get_status_display()})"

    @property
    def full_shipping_address(self):
        parts = [self.shipping_address_line1]
        if self.shipping_address_line2:
            parts.append(self.shipping_address_line2)
        if self.shipping_landmark:
            parts.append(f"Near {self.shipping_landmark}")
        parts.append(f"{self.shipping_city}, {self.shipping_state} - {self.shipping_pincode}")
        return ", ".join(parts)

    @property
    def can_cancel(self):
        return self.status in [self.STATUS_PENDING, self.STATUS_CONFIRMED]

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def get_whatsapp_text(self):
        items_text = []
        for idx, item in enumerate(self.items.all(), 1):
            variant_parts = []
            if item.selected_size:
                variant_parts.append(f"Size: {item.selected_size}")
            if item.selected_color:
                variant_parts.append(f"Color: {item.selected_color}")
            var_str = f" [{', '.join(variant_parts)}]" if variant_parts else ""
            items_text.append(f"{idx}. {item.product_name}{var_str} x {item.quantity} = ₹{item.subtotal}")
        items_str = "\n".join(items_text)

        message = (
            f"🛍️ *Plat4Sale — New Order Confirmed!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 *Order ID:* {self.order_number}\n"
            f"👤 *Customer:* {self.customer_name}\n"
            f"📞 *Phone:* {self.customer_phone}\n\n"
            f"📦 *Ordered Items:*\n{items_str}\n\n"
            f"💵 *Subtotal:* ₹{self.subtotal}\n"
            f"🚚 *Delivery:* {'FREE' if self.shipping_fee == 0 else f'₹{self.shipping_fee}'}\n"
            f"💰 *Total Amount:* ₹{self.total_amount}\n"
            f"💳 *Payment Mode:* {self.get_payment_method_display()}\n\n"
            f"📍 *Delivery Address:*\n{self.full_shipping_address}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Please process my order. Thank you for choosing Plat4Sale!"
        )
        return message

    def get_whatsapp_url(self, business_phone="919876543210"):
        msg = urllib.parse.quote(self.get_whatsapp_text())
        clean_phone = business_phone.replace("+", "").replace(" ", "").replace("-", "")
        return f"https://wa.me/{clean_phone}?text={msg}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items")
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=50, blank=True)
    selected_size = models.CharField(max_length=50, blank=True, default="")
    selected_color = models.CharField(max_length=50, blank=True, default="")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.product_name} x {self.quantity} ({self.order.order_number})"
