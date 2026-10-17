from django import forms
from apps.catalog.models import Product, ProductImage, Category, Banner
from apps.core.models import StoreSettings


class ProductAdminForm(forms.ModelForm):
    primary_image = forms.ImageField(required=False, label="Primary Product Photo")
    additional_image_1 = forms.ImageField(required=False, label="Gallery Photo 2")
    additional_image_2 = forms.ImageField(required=False, label="Gallery Photo 3")

    class Meta:
        model = Product
        fields = [
            "name", "category", "sku", "price", "sale_price",
            "stock", "is_featured", "is_bestseller", "is_new_arrival", "is_active",
            "short_description", "description",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "E.g. Sonic Sound Wireless Pro"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "sku": forms.TextInput(attrs={"class": "form-control", "placeholder": "E.g. PS-ELEC-001"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "placeholder": "MRP (Original Price)"}),
            "sale_price": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Offer Price (Leave empty if no discount)"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Stock quantity"}),
            "short_description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Catchy 1-line feature summary"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Detailed product description and specs..."}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_bestseller": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_new_arrival": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "icon_class", "image", "description", "is_featured", "is_active", "sort_order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Category Name"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "category-slug (auto-generated if empty)"}),
            "icon_class": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. bi-phone, bi-laptop, bi-bag, bi-watch"}),
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
            "store_name", "tagline", "whatsapp_number", "support_phone",
            "support_email", "currency_symbol", "free_shipping_threshold",
            "standard_shipping_fee", "announcement_text", "announcement_active", "address"
        ]
        widgets = {
            "store_name": forms.TextInput(attrs={"class": "form-control"}),
            "tagline": forms.TextInput(attrs={"class": "form-control"}),
            "whatsapp_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "919876543210 (Country code + phone without +)"}),
            "support_phone": forms.TextInput(attrs={"class": "form-control"}),
            "support_email": forms.EmailInput(attrs={"class": "form-control"}),
            "currency_symbol": forms.TextInput(attrs={"class": "form-control"}),
            "free_shipping_threshold": forms.NumberInput(attrs={"class": "form-control"}),
            "standard_shipping_fee": forms.NumberInput(attrs={"class": "form-control"}),
            "announcement_text": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "announcement_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
