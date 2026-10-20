from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    icon_class = models.CharField(max_length=50, default="bi-grid", help_text="Bootstrap icon class e.g. bi-phone, bi-laptop, bi-bag")
    has_sizes = models.BooleanField(default=False, verbose_name="Requires Sizes (e.g., Fashion, Clothing, Shoes)")
    is_featured = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:category_detail", kwargs={"slug": self.slug})

    @property
    def seo_title(self):
        return f"{self.name} Collection — Buy Online | Plat4Sale"

    @property
    def seo_description(self):
        if self.description:
            return self.description[:160]
        return f"Shop genuine {self.name} online at Plat4Sale with best prices and WhatsApp ordering."


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU / Item Code")
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Original Price (MRP)")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Sale / Offer Price")
    stock = models.PositiveIntegerField(default=10, verbose_name="Stock Quantity")

    # Fashion / Variant attributes
    available_sizes = models.CharField(max_length=255, blank=True, help_text="Comma-separated sizes e.g. S, M, L, XL, XXL or 38, 40, 42")
    available_colors = models.CharField(max_length=255, blank=True, help_text="Comma-separated colors e.g. Black, White, Navy Blue, Maroon")

    is_featured = models.BooleanField(default=False, verbose_name="Featured Product")
    is_bestseller = models.BooleanField(default=False, verbose_name="Best Seller")
    is_new_arrival = models.BooleanField(default=False, verbose_name="New Arrival")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Views / Click Count")

    # Search Engine Optimization (SEO) attributes
    meta_title = models.CharField(max_length=200, blank=True, verbose_name="SEO Meta Title", help_text="Custom title tag for search engines (optional)")
    meta_description = models.CharField(max_length=320, blank=True, verbose_name="SEO Meta Description", help_text="Custom description for search engines (optional)")
    meta_keywords = models.CharField(max_length=255, blank=True, verbose_name="SEO Meta Keywords", help_text="Custom comma-separated keywords (optional)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    @property
    def current_price(self):
        if self.sale_price and self.sale_price < self.price:
            return self.sale_price
        return self.price

    @property
    def discount_percentage(self):
        if self.sale_price and self.sale_price < self.price:
            diff = self.price - self.sale_price
            return int((diff / self.price) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= 5

    @property
    def sizes_list(self):
        if self.available_sizes:
            return [s.strip() for s in self.available_sizes.split(",") if s.strip()]
        return []

    @property
    def colors_list(self):
        if self.available_colors:
            return [c.strip() for c in self.available_colors.split(",") if c.strip()]
        return []

    @property
    def primary_image(self):
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()

    @property
    def average_rating(self):
        approved = self.reviews.filter(is_approved=True)
        if approved.exists():
            avg = approved.aggregate(models.Avg("rating"))["rating__avg"]
            return round(avg, 1) if avg else 5.0
        return 5.0

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()

    @property
    def seo_title(self):
        return self.meta_title or f"{self.name} — Buy Online at Best Price | Plat4Sale"

    @property
    def seo_description(self):
        if self.meta_description:
            return self.meta_description
        desc = self.short_description or self.description or ""
        clean_desc = desc[:155].strip()
        return clean_desc or f"Buy {self.name} online at ₹{self.current_price}. Fast delivery and WhatsApp order available at Plat4Sale."


class ProductImage(models.Model):
    MEDIA_TYPE_CHOICES = [
        ("image", "Image"),
        ("video", "Video"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default="image")
    image = models.FileField(upload_to="products/", help_text="Product image or video file (Slot 1 compulsory image, Slots 2-10 optional images or videos)")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-is_primary", "sort_order", "id"]

    def __str__(self):
        return f"{self.get_media_type_display()} for {self.product.name}"

    @property
    def is_video(self):
        if self.media_type == "video":
            return True
        if self.image:
            ext = self.image.name.lower().split(".")[-1]
            return ext in ["mp4", "webm", "mov", "ogg"]
        return False

    def save(self, *args, **kwargs):
        # Auto-detect video format
        if self.image:
            ext = self.image.name.lower().split(".")[-1]
            if ext in ["mp4", "webm", "mov", "ogg"]:
                self.media_type = "video"
            else:
                self.media_type = "image"

        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class Banner(models.Model):
    PLACEMENT_CHOICES = [
        ("hero", "Hero Slider"),
        ("promo_grid", "Promotional Grid"),
        ("promo_strip", "Promotional Strip / Footer Banner"),
    ]

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    badge_text = models.CharField(max_length=50, blank=True, help_text="e.g. MEGA DEAL, NEW LAUNCH")
    image = models.ImageField(upload_to="banners/")
    button_text = models.CharField(max_length=50, default="SHOP NOW")
    button_url = models.CharField(max_length=255, default="/products/")
    placement = models.CharField(max_length=30, choices=PLACEMENT_CHOICES, default="hero")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_placement_display()})"


class ProductClick(models.Model):
    """
    Tracks every individual click / view on a product with timestamps
    for date-based analytics (Today, Week, Month, Year, Custom Dates).
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="clicks")
    session_key = models.CharField(max_length=64, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Product Click"
        verbose_name_plural = "Product Clicks"

    def __str__(self):
        return f"Click on {self.product.name} at {self.timestamp}"
