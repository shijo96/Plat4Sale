from django.http import HttpResponse
from django.utils import timezone
from apps.core.models import StoreSettings
from apps.catalog.models import Product, Category


def robots_txt_view(request):
    store = StoreSettings.get_settings()
    base_url = (store.canonical_base_url or "https://plat4sale.com").rstrip("/")
    content = f"""User-agent: *
Disallow: /dashboard/
Disallow: /django-admin/
Disallow: /accounts/
Disallow: /cart/
Disallow: /wishlist/
Disallow: /orders/
Disallow: /api/
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
    return HttpResponse(content.strip(), content_type="text/plain; charset=utf-8")


def sitemap_xml_view(request):
    store = StoreSettings.get_settings()
    base_url = (store.canonical_base_url or "https://plat4sale.com").rstrip("/")
    now_iso = timezone.now().strftime("%Y-%m-%d")

    urls = [
        {"loc": f"{base_url}/", "changefreq": "daily", "priority": "1.0", "lastmod": now_iso},
        {"loc": f"{base_url}/products/", "changefreq": "daily", "priority": "0.9", "lastmod": now_iso},
    ]

    for cat in Category.objects.filter(is_active=True):
        urls.append({
            "loc": f"{base_url}{cat.get_absolute_url()}",
            "changefreq": "weekly",
            "priority": "0.8",
            "lastmod": now_iso,
        })

    for prod in Product.objects.filter(is_active=True):
        prod_date = prod.updated_at.strftime("%Y-%m-%d") if prod.updated_at else now_iso
        urls.append({
            "loc": f"{base_url}{prod.get_absolute_url()}",
            "changefreq": "daily",
            "priority": "0.85",
            "lastmod": prod_date,
        })

    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{u['loc']}</loc>")
        xml_lines.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        xml_lines.append(f"    <changefreq>{u['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{u['priority']}</priority>")
        xml_lines.append("  </url>")
    xml_lines.append("</urlset>")

    return HttpResponse("\n".join(xml_lines), content_type="application/xml; charset=utf-8")
