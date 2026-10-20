import os
import django
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.accounts.models import User, Address
from apps.catalog.models import Category, Product, ProductImage, Banner
from apps.core.models import StoreSettings
from apps.reviews.models import Review


def run_seed():
    print("🌱 Seeding Plat4Sale database...")

    # 1. Store Settings
    store, created = StoreSettings.objects.get_or_create(id=1)
    store.store_name = "Plat4Sale"
    store.tagline = "FIND • SHOP • LOVE"
    store.whatsapp_number = "919876543210"
    store.support_phone = "+91 98765 43210"
    store.support_email = "orders@plat4sale.com"
    store.currency_symbol = "₹"
    store.free_shipping_threshold = Decimal("499.00")
    store.standard_shipping_fee = Decimal("49.00")
    store.announcement_text = "⚡ Special Offers • New Arrivals • Free Delivery on orders over ₹499 • WhatsApp Support Available!"
    store.announcement_active = True
    store.save()
    print("✓ Store settings configured.")

    # 2. Users: Admin and Customer
    admin_user = User.objects.filter(username="admin").first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@plat4sale.com",
            password="adminpassword123",
            first_name="Store",
            last_name="Manager",
            phone="9876543210"
        )
        print("✓ Superuser 'admin' created (password: adminpassword123).")
    else:
        admin_user.set_password("adminpassword123")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

    customer = User.objects.filter(username="shijo").first()
    if not customer:
        customer = User.objects.create_user(
            username="shijo",
            email="shijo@example.com",
            password="customerpass123",
            first_name="Shijo",
            last_name="John",
            phone="9876543210"
        )
        print("✓ Customer 'shijo' created (password: customerpass123).")

    # Customer default address
    if not customer.addresses.exists():
        Address.objects.create(
            user=customer,
            full_name="Shijo John",
            phone="9876543210",
            address_line1="Plat4Sale Apartment, Suite 4B",
            address_line2="Marine Drive, MG Road",
            landmark="Near Metro Station",
            city="Kochi",
            state="Kerala",
            pincode="682011",
            is_default=True,
        )
        print("✓ Saved default delivery address for 'shijo'.")

    # 3. Categories
    categories_data = [
        {"name": "Electronics", "slug": "electronics", "icon_class": "bi-headphones", "desc": "High quality audio, headphones and tech gear"},
        {"name": "Footwear & Sports", "slug": "footwear-sports", "icon_class": "bi-award", "desc": "Running sneakers, casual shoes, and athletic wear"},
        {"name": "Smart Wearables", "slug": "smart-wearables", "icon_class": "bi-smartwatch", "desc": "Fitness trackers, OLED smart watches, smart rings"},
        {"name": "Bags & Travel", "slug": "bags-travel", "icon_class": "bi-backpack", "desc": "Commuter backpacks, travel duffels, and laptop sleeves"},
        {"name": "Fashion & Apparel", "slug": "fashion-apparel", "icon_class": "bi-tag", "desc": "Trendy apparel, streetwear, jackets and everyday essentials"},
        {"name": "Home & Living", "slug": "home-living", "icon_class": "bi-house-heart", "desc": "Aesthetic home decor, modern lighting, kitchenware"},
    ]

    cat_map = {}
    for idx, c in enumerate(categories_data):
        cat, _ = Category.objects.get_or_create(slug=c["slug"], defaults={
            "name": c["name"],
            "description": c["desc"],
            "icon_class": c["icon_class"],
            "is_featured": True,
            "is_active": True,
            "sort_order": idx,
        })
        cat_map[c["slug"]] = cat
    print("✓ Categories configured.")

    # 4. Products with Generated Studio Photos
    products_data = [
        {
            "name": "Sonic Sound Wireless Noise-Cancelling Headphones",
            "slug": "sonic-sound-wireless-headphones",
            "sku": "PS-ELEC-001",
            "category": cat_map["electronics"],
            "short_description": "Matte black over-ear wireless headphones with active noise cancellation, 40h battery, and deep bass acoustics.",
            "description": "Experience pure studio sound with the Sonic Sound Pro Wireless Headphones. Equipped with 40mm neodymium dynamic drivers, active hybrid noise cancellation, plush memory foam ear cushions, and Bluetooth 5.3 instant pairing. Built-in ultra-clear microphones make hand-free calling crystal clear.",
            "price": Decimal("2999.00"),
            "sale_price": Decimal("1499.00"),
            "stock": 25,
            "is_featured": True,
            "is_bestseller": True,
            "is_new_arrival": True,
            "image": "products/headphones.jpg",
        },
        {
            "name": "SpeedPro 5 Athletic Running Sneakers",
            "slug": "speedpro-5-athletic-sneakers",
            "sku": "PS-SHOE-002",
            "category": cat_map["footwear-sports"],
            "short_description": "Ultralight breathable mesh running sneakers with responsive FlyteFoam cushioning and neon grip accents.",
            "description": "Step into maximum comfort with SpeedPro 5. Engineered with breathable jacquard knit mesh, responsive energy-return foam midsole, anti-skid rubber outsole, and lightweight ergonomics. Ideal for morning runs, gym workouts, or casual everyday street style.",
            "price": Decimal("3999.00"),
            "sale_price": Decimal("1999.00"),
            "stock": 18,
            "is_featured": True,
            "is_bestseller": True,
            "is_new_arrival": False,
            "image": "products/sneakers.jpg",
        },
        {
            "name": "FitTrack Pulse Smart Watch Pro OLED",
            "slug": "fittrack-pulse-smart-watch-pro",
            "sku": "PS-WATCH-003",
            "category": cat_map["smart-wearables"],
            "short_description": "Sleek fitness smartwatch with 1.95-inch AMOLED curved display, SpO2 sensor, sleep tracker, and Bluetooth calling.",
            "description": "Take control of your daily vitality. The FitTrack Pulse features a vibrant always-on AMOLED display, 24/7 heart rate and blood oxygen monitoring, 100+ multi-sport workout modes, water-resistant IP68 casing, customizable watch faces, and 7-day battery life on a single charge.",
            "price": Decimal("4499.00"),
            "sale_price": Decimal("2499.00"),
            "stock": 14,
            "is_featured": True,
            "is_bestseller": False,
            "is_new_arrival": True,
            "image": "products/smartwatch.jpg",
        },
        {
            "name": "Aether Urban Waterproof Commuter Backpack",
            "slug": "aether-urban-commuter-backpack",
            "sku": "PS-BAG-004",
            "category": cat_map["bags-travel"],
            "short_description": "Minimalist all-weather commuter laptop backpack with anti-theft hidden pocket, padded straps, and USB charge port.",
            "description": "Crafted from ballistic waterproof oxford fabric with genuine leather pull tabs. Fits up to 16-inch laptops in a dedicated fleece-lined compartment. Features ergonomic breathable lumbar support, luggage trolley pass-through strap, and water bottle side pockets.",
            "price": Decimal("2499.00"),
            "sale_price": Decimal("1299.00"),
            "stock": 32,
            "is_featured": True,
            "is_bestseller": True,
            "is_new_arrival": True,
            "image": "products/backpack.jpg",
        },
    ]

    for p_data in products_data:
        img_rel_path = p_data.pop("image")
        prod, _ = Product.objects.get_or_create(slug=p_data["slug"], defaults=p_data)
        if not prod.images.exists():
            ProductImage.objects.create(
                product=prod,
                image=img_rel_path,
                alt_text=prod.name,
                is_primary=True,
                sort_order=0
            )

    print("✓ Products and images seeded.")

    # 5. Hero Banner
    if not Banner.objects.filter(placement="hero").exists():
        Banner.objects.create(
            title="Discover Your Next Favourite",
            subtitle="Shop the latest gadgets, trendy footwear & lifestyle products at unbelievable prices.",
            badge_text="MEGA SALE • UP TO 50% OFF",
            image="banners/hero_tech.jpg",
            button_text="SHOP NOW →",
            button_url="/products/",
            placement="hero",
            is_active=True,
            sort_order=0
        )
        print("✓ Hero banner configured.")

    print("\n🎉 Plat4Sale database setup complete!")
    print("==================================================")
    print("Admin Portal URL:    http://127.0.0.1:8000/dashboard/")
    print("Admin Login:         admin / adminpassword123")
    print("Customer Login:      shijo / customerpass123")
    print("Public Store URL:    http://127.0.0.1:8000/")
    print("==================================================")


if __name__ == "__main__":
    run_seed()
