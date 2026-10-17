# Plat4Sale — Dynamic E-Commerce Web Application

**Plat4Sale** is an Amazon/Flipkart-inspired, database-driven modern E-Commerce web application built using **Python + Django**, styled with **Bootstrap 5.3 + Custom CSS**, and pre-configured for **GitHub** version control and **Vercel** serverless cloud deployment.

> **Slogan:** *FIND • SHOP • LOVE*

---

## 🚀 Key Features

### 1. Public Storefront (No Login Required)
- **Header & Navigation:** Sticky top announcement bar with support hotline, brand emblem logo, live instant autocomplete search with category filter, wishlist counter badge, and shopping cart counter with dynamic subtotal.
- **Department Ribbon:** Fast navigation across all departments (Electronics, Footwear & Sports, Smart Wearables, Bags & Travel, Fashion, Home & Living).
- **Hero Carousel:** Responsive dynamic promotional banners with direct call-to-actions.
- **Product Catalog:** Product cards with discount badges (`% OFF`), Best Seller tags, live AJAX wishlist toggles, and instant AJAX "Add to Cart" with toast notifications.
- **Product Details:** High-resolution product image gallery with thumbnail switcher, stock status (In Stock / Low Stock Alert / Out of Stock), pricing breakdown, technical specifications table, customer reviews breakdown (5★ - 1★ progress bars), direct "Buy Now" checkout, and a **"Order / Inquire on WhatsApp"** direct button.
- **Filtering & Sorting:** Filter products by category, price range, and stock availability; sort by popularity, price (low/high), or newest arrivals.

### 2. Shopping Cart & Wishlist
- **Dynamic Guest & User Cart:** Supports anonymous visitors with seamless session-to-user cart merging upon registration or login.
- **Free Delivery Goal Tracker:** Interactive progress bar calculating amount needed to unlock free shipping.
- **Quantity Adjuster:** Increase/decrease quantities with real-time stock validation.
- **Customer Wishlist:** Dedicated wishlist management with 1-click "Move to Cart".

### 3. Checkout & WhatsApp Ordering Integration
- **Delivery Address Management:** Select from saved addresses or input a new delivery destination on the fly.
- **Payment Method:** Cash on Delivery (COD) default support + UPI QR code option.
- **Transactional Safety:** Uses `transaction.atomic()` to guarantee order creation, snapshotting unit prices and SKU, and safely decrementing inventory stock.
- **Automated WhatsApp Order Slip:** Generates pre-formatted WhatsApp message URLs with Order ID (`PS-XXXXX`), customer name, itemized products, total amount, payment mode, and delivery address to send to the store's WhatsApp business number.
- **Live Shipment Tracker:** Visual 5-stage shipment roadmap (*Placed → Confirmed → Processing → Shipped → Delivered*).

### 4. Custom Management Admin Panel (`/dashboard/`)
*Completely separate and distinct from Django's built-in `/django-admin/`:*
- **Analytics Overview:** Real-time metrics for Total Revenue (₹), Total Orders, Pending Orders, Catalog Products, Low Stock alerts (< 5 items), Registered Customers, and Pending Reviews.
- **Product Management:** Searchable and filterable catalog, add new products with multi-image upload, update inventory, and manage prices/discounts.
- **Category Management:** Create, edit, and organize categories with Bootstrap icon classes.
- **Order Management:** View order details, update shipment stages, toggle payment status (Paid / Unpaid), and generate **Printable Tax Invoices**.
- **Customer Directory:** Track registered customer order counts, total spend, and launch 1-click WhatsApp customer chats.
- **Review Moderation:** Approve, hide, or delete customer reviews.
- **Promotional Banners:** Manage homepage slider graphics, links, and deal badges.
- **Store & WhatsApp Settings:** Configure business WhatsApp phone number, free delivery threshold, and announcement ticker text.

---

## 📂 Project Architecture

```
My_WebSite/
│
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── vercel.json
├── build_files.sh
├── seed_db.py
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── accounts/       # Custom User model, addresses, authentication
│   ├── catalog/        # Categories, Products, ProductImages, Banners
│   ├── cart/           # Guest & User Cart, CartItems
│   ├── wishlist/       # Customer Wishlist
│   ├── orders/         # Orders, OrderItems, Checkout, WhatsApp integration
│   ├── reviews/        # Customer ratings and reviews
│   ├── dashboard/      # Custom Admin Panel & Store Management
│   └── core/           # StoreSettings, Global context processors
│
├── templates/
│   ├── base.html
│   ├── includes/       # navbar, footer, product_card, messages
│   ├── store/          # home, product_list, product_detail, category_detail
│   ├── accounts/       # login, register
│   ├── cart/           # cart_detail
│   ├── wishlist/       # wishlist
│   ├── orders/         # checkout, order_confirmation, my_orders, order_detail
│   ├── customer/       # profile, addresses, address_form, change_password
│   └── dashboard/      # home, products, categories, orders, customers, reviews, banners, settings
│
├── static/
│   ├── css/            # main.css (Plat4Sale Design System)
│   ├── js/             # main.js (Live search, AJAX cart, wishlist, toasts)
│   └── images/         # Logo & branding assets
│
└── media/              # Product photos & promotional banners
```

---

## 💻 Local Quickstart

### 1. Activate Environment
```bash
source .venv/bin/activate
```

### 2. Apply Migrations & Seed Database
```bash
python manage.py migrate
python seed_db.py
```

### 3. Start Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 🔑 Default Login Credentials

| Role | Username | Password | Access URL |
| :--- | :--- | :--- | :--- |
| **Admin / Manager** | `admin` | `adminpassword123` | [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/) |
| **Customer** | `shijo` | `customerpass123` | [http://127.0.0.1:8000/accounts/login/](http://127.0.0.1:8000/accounts/login/) |

---

## 🚀 GitHub & Vercel Deployment Guide

### Step 1: Push Code to GitHub
```bash
git init
git add .
git commit -m "Initial commit: Complete Plat4Sale E-Commerce Platform"
git branch -M main
git remote add origin https://github.com/<your-username>/plat4sale.git
git push -u origin main
```

### Step 2: Deploy to Vercel
1. Log in to [Vercel](https://vercel.com) and click **"Add New Project"**.
2. Select your `plat4sale` GitHub repository.
3. In **Project Settings → Environment Variables**, configure:
   ```env
   DJANGO_SECRET_KEY=your-production-secret-key-here
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=.vercel.app,your-custom-domain.com
   DATABASE_URL=postgres://user:password@host:5432/dbname
   WHATSAPP_NUMBER=919876543210
   ```
4. Click **Deploy**. Vercel will build using `vercel.json` and `build_files.sh`.

### Production Database Recommendation
For production on Vercel (serverless environment), connect a managed PostgreSQL instance such as:
- **Neon Serverless Postgres** ([neon.tech](https://neon.tech))
- **Supabase Postgres** ([supabase.com](https://supabase.com))
- **Vercel Postgres**

Provide the connection string in the `DATABASE_URL` environment variable. The project automatically configures connection pooling via `dj-database-url`.
