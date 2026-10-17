from django.db import models


class StoreSettings(models.Model):
    store_name = models.CharField(max_length=100, default="Plat4Sale")
    tagline = models.CharField(max_length=200, default="FIND • SHOP • LOVE")
    whatsapp_number = models.CharField(max_length=25, default="919876543210", help_text="Number with country code (e.g. 919876543210) for WhatsApp click to chat")
    support_phone = models.CharField(max_length=50, default="+91 98765 43210")
    support_email = models.EmailField(default="support@plat4sale.com")
    currency_symbol = models.CharField(max_length=10, default="₹")
    free_shipping_threshold = models.DecimalField(max_digits=8, decimal_places=2, default=499.00)
    standard_shipping_fee = models.DecimalField(max_digits=8, decimal_places=2, default=49.00)
    announcement_text = models.CharField(max_length=255, default="⚡ Super Deal Days: Up to 60% OFF on Top Electronics & Fashion! Free Delivery on orders above ₹499.")
    announcement_active = models.BooleanField(default=True)
    address = models.CharField(max_length=255, default="Plat4Sale E-Commerce Hub, Kochi, Kerala, India")

    class Meta:
        verbose_name = "Store Settings"
        verbose_name_plural = "Store Settings"

    def __str__(self):
        return f"{self.store_name} Settings"

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj
