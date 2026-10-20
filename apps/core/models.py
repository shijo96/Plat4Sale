from django.db import models


class StoreSettings(models.Model):
    store_name = models.CharField(max_length=100, default="Plat4Sale")
    tagline = models.CharField(max_length=200, default="FIND • SHOP • LOVE")
    whatsapp_number = models.CharField(max_length=25, default="919876543210", help_text="Number with country code (e.g. 919876543210) for customer WhatsApp click to chat")
    admin_whatsapp_number = models.CharField(max_length=25, default="919876543210", help_text="Admin WhatsApp number to receive automated order slips and low-stock alerts")
    support_phone = models.CharField(max_length=50, default="+91 98765 43210")
    support_email = models.EmailField(default="support@plat4sale.com")
    currency_symbol = models.CharField(max_length=10, default="₹")
    free_shipping_threshold = models.DecimalField(max_digits=8, decimal_places=2, default=499.00)
    standard_shipping_fee = models.DecimalField(max_digits=8, decimal_places=2, default=49.00)
    announcement_text = models.CharField(max_length=255, default="⚡ Super Deal Days: Up to 60% OFF on Top Electronics & Fashion! Free Delivery on orders above ₹499.")
    announcement_active = models.BooleanField(default=True)
    address = models.CharField(max_length=255, default="Plat4Sale E-Commerce Hub, Kochi, Kerala, India")

    # Payment Methods toggles
    whatsapp_only_orders = models.BooleanField(default=True, verbose_name="Only WhatsApp Orders (Customer can only order via WhatsApp)")
    cod_enabled = models.BooleanField(default=False, verbose_name="Enable Cash on Delivery (COD)")
    online_payment_enabled = models.BooleanField(default=False, verbose_name="Enable Online / UPI Payment")

    # Automated WhatsApp notifications
    auto_whatsapp_notification = models.BooleanField(default=True, verbose_name="Automatic order notification to admin WhatsApp")
    low_stock_whatsapp_alert = models.BooleanField(default=True, verbose_name="Send WhatsApp alert when product stock drops <= 5")

    # Search Engine Optimization (SEO) & Webmaster Configuration
    seo_meta_title = models.CharField(
        max_length=200,
        default="Plat4Sale — Buy Online with WhatsApp Order | Best Deals in India",
        verbose_name="Default SEO Meta Title",
        help_text="The title tag shown in Google search results and browser tabs"
    )
    seo_meta_description = models.TextField(
        default="Discover top electronics, trendy footwear, smart wearables & lifestyle accessories at Plat4Sale. Enjoy express delivery, cash on delivery, and instant WhatsApp ordering.",
        verbose_name="Default SEO Meta Description",
        help_text="Summary description shown beneath your website title in search engine results (150-160 characters recommended)"
    )
    seo_meta_keywords = models.CharField(
        max_length=350,
        default="plat4sale, online shopping, electronics, sneakers, headphones, smart watch, kerala, whatsapp shopping, cash on delivery",
        verbose_name="SEO Meta Keywords",
        help_text="Comma-separated keywords for search engine indexing"
    )
    seo_og_image = models.ImageField(
        upload_to="seo/",
        blank=True,
        null=True,
        verbose_name="Social Share Banner (OG Image)",
        help_text="Image preview shown when website link is shared on WhatsApp, Facebook, Instagram, Twitter (1200x630px recommended)"
    )
    google_search_console_code = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Google Search Console Verification Tag",
        help_text="Verification token for Google Search Console (e.g. google-site-verification content string)"
    )
    google_analytics_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Google Analytics / Tag ID",
        help_text="Measurement ID from Google Analytics (e.g. G-XXXXXXXXXX)"
    )
    canonical_base_url = models.URLField(
        max_length=200,
        default="https://plat4sale.com",
        verbose_name="Canonical Base URL",
        help_text="The primary live domain URL used for canonical link tags (e.g. https://plat4sale.com)"
    )

    class Meta:
        verbose_name = "Store Settings"
        verbose_name_plural = "Store Settings"

    def __str__(self):
        return f"{self.store_name} Settings"

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj


class SiteVisit(models.Model):
    """
    Tracks visitor traffic, pageviews, and live active users across the store.
    """
    session_key = models.CharField(max_length=64, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="site_visits")
    path = models.CharField(max_length=255, db_index=True)
    user_agent = models.CharField(max_length=255, blank=True)
    referer = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    last_activity = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Site Visit"
        verbose_name_plural = "Site Visits"

    def __str__(self):
        return f"Visit {self.path} by {self.session_key[:8]} at {self.timestamp}"
