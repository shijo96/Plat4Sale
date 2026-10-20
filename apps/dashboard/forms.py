from django import forms
from apps.catalog.models import Product, ProductImage, Category, Banner
from apps.core.models import StoreSettings


class ProductAdminForm(forms.ModelForm):
    # Slot 1: Compulsory primary image
    primary_image = forms.ImageField(
        required=False,
        label="Slot 1: Main Product Image (Compulsory)",
        help_text="Required. Format: JPG, PNG, WEBP. Max size: 5MB. Recommended resolution: 1000x1000px."
    )
    # Slots 2 to 10: Optional Images or Videos
    media_2 = forms.FileField(required=False, label="Slot 2 (Optional - Image or Video)")
    media_3 = forms.FileField(required=False, label="Slot 3 (Optional - Image or Video)")
    media_4 = forms.FileField(required=False, label="Slot 4 (Optional - Image or Video)")
    media_5 = forms.FileField(required=False, label="Slot 5 (Optional - Image or Video)")
    media_6 = forms.FileField(required=False, label="Slot 6 (Optional - Image or Video)")
    media_7 = forms.FileField(required=False, label="Slot 7 (Optional - Image or Video)")
    media_8 = forms.FileField(required=False, label="Slot 8 (Optional - Image or Video)")
    media_9 = forms.FileField(required=False, label="Slot 9 (Optional - Image or Video)")
    media_10 = forms.FileField(required=False, label="Slot 10 (Optional - Image or Video)")

    class Meta:
        model = Product
        fields = [
            "name", "category", "sku", "price", "sale_price",
            "stock", "available_sizes", "available_colors",
            "is_featured", "is_bestseller", "is_new_arrival", "is_active",
            "short_description", "description",
            "meta_title", "meta_description", "meta_keywords",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "E.g. Sonic Sound Wireless Pro"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "sku": forms.TextInput(attrs={"class": "form-control", "placeholder": "E.g. PS-ELEC-001"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "placeholder": "MRP (Original Price)"}),
            "sale_price": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Offer Price (Leave empty if no discount)"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Available Stock Units"}),
            "available_sizes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Comma-separated e.g. S, M, L, XL, XXL or 38, 40, 42"}),
            "available_colors": forms.TextInput(attrs={"class": "form-control", "placeholder": "Comma-separated e.g. Black, White, Navy Blue, Red"}),
            "short_description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Catchy 1-line feature summary"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Detailed product description and specs..."}),
            "meta_title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Custom SEO Title (Optional)"}),
            "meta_description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Custom Search Engine Description (Optional)"}),
            "meta_keywords": forms.TextInput(attrs={"class": "form-control", "placeholder": "keywords, separated, by, commas"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_bestseller": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_new_arrival": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        primary_image = cleaned_data.get("primary_image")
        # If creating a new product and no primary image is provided
        if not self.instance.pk and not primary_image:
            self.add_error("primary_image", "Slot 1 (Main Product Image) is compulsory. Please upload a photo.")
        return cleaned_data


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "icon_class", "has_sizes", "image", "description", "is_featured", "is_active", "sort_order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Category Name"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "category-slug (auto-generated if empty)"}),
            "icon_class": forms.TextInput(attrs={"class": "form-control", "id": "icon_class_input", "placeholder": "e.g. bi-bag, bi-headphones, bi-award"}),
            "has_sizes": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class BannerAdminForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ["title", "subtitle", "badge_text", "image", "button_text", "button_url", "placement", "is_active", "sort_order"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Main Banner Headline"}),
            "subtitle": forms.TextInput(attrs={"class": "form-control", "placeholder": "Secondary text / deal description"}),
            "badge_text": forms.TextInput(attrs={"class": "form-control", "placeholder": "E.g. MEGA DEAL 50% OFF"}),
            "button_text": forms.TextInput(attrs={"class": "form-control", "placeholder": "E.g. SHOP NOW"}),
            "button_url": forms.TextInput(attrs={"class": "form-control", "placeholder": "/products/ or /category/electronics/"}),
            "placement": forms.Select(attrs={"class": "form-select"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class StoreSettingsForm(forms.ModelForm):
    class Meta:
        model = StoreSettings
        fields = [
            "store_name", "tagline", "whatsapp_number", "admin_whatsapp_number",
            "support_phone", "support_email", "currency_symbol", "free_shipping_threshold",
            "standard_shipping_fee", "announcement_text", "announcement_active", "address",
            "whatsapp_only_orders", "cod_enabled", "online_payment_enabled",
            "auto_whatsapp_notification", "low_stock_whatsapp_alert",
            "seo_meta_title", "seo_meta_description", "seo_meta_keywords", "seo_og_image",
            "google_search_console_code", "google_analytics_id", "canonical_base_url"
        ]
        widgets = {
            "store_name": forms.TextInput(attrs={"class": "form-control"}),
            "tagline": forms.TextInput(attrs={"class": "form-control"}),
            "whatsapp_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "919876543210 (Customer chat number)"}),
            "admin_whatsapp_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "919876543210 (Admin alerts number)"}),
            "support_phone": forms.TextInput(attrs={"class": "form-control"}),
            "support_email": forms.EmailInput(attrs={"class": "form-control"}),
            "currency_symbol": forms.TextInput(attrs={"class": "form-control"}),
            "free_shipping_threshold": forms.NumberInput(attrs={"class": "form-control"}),
            "standard_shipping_fee": forms.NumberInput(attrs={"class": "form-control"}),
            "announcement_text": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "announcement_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "whatsapp_only_orders": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "cod_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "online_payment_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "auto_whatsapp_notification": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "low_stock_whatsapp_alert": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "seo_meta_title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Default SEO Meta Title for search engines"}),
            "seo_meta_description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Search engine summary description (150-160 characters)"}),
            "seo_meta_keywords": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. online shopping, electronics, kerala"}),
            "seo_og_image": forms.FileInput(attrs={"class": "form-control"}),
            "google_search_console_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. google-site-verification token"}),
            "google_analytics_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. G-XXXXXXXXXX"}),
            "canonical_base_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://plat4sale.com"}),
        }
