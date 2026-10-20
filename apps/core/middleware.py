from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.urls import resolve
from .models import SiteVisit
from apps.catalog.models import Product, ProductClick


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class TrafficTrackingMiddleware:
    """
    Real-time website traffic & visitor tracking middleware.
    Tracks live active customers, unique visitors, pageviews,
    and product detail views/clicks across the store.
    """
    EXCLUDED_PREFIXES = (
        "/static/",
        "/media/",
        "/admin/",
        "/dashboard/",
        "/api/",
        "/favicon.ico",
        "/__debug__/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Ignore static assets, background APIs, and administrative paths
        if any(path.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES):
            return self.get_response(request)

        # Ignore AJAX background calls from counting as pageviews
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return self.get_response(request)

        # Ignore staff / admin users so internal store maintenance doesn't pollute real customer traffic
        if getattr(request, "user", None) and request.user.is_authenticated and request.user.is_staff:
            return self.get_response(request)

        # Ensure session exists to track unique customers and live status
        if not request.session.session_key:
            try:
                request.session.save()
            except Exception:
                pass

        session_key = request.session.session_key or "anonymous"
        ip = get_client_ip(request)
        user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:250]
        referer = request.META.get("HTTP_REFERER", "")[:250]
        now = timezone.now()

        # Update or record page visit
        try:
            recent_visit = SiteVisit.objects.filter(
                session_key=session_key,
                path=path,
                timestamp__gte=now - timedelta(minutes=3),
            ).first()

            if recent_visit:
                SiteVisit.objects.filter(id=recent_visit.id).update(last_activity=now)
            else:
                SiteVisit.objects.create(
                    session_key=session_key,
                    ip_address=ip,
                    user=user,
                    path=path,
                    user_agent=user_agent,
                    referer=referer,
                )

            # Check if this request is a Product Detail page view/click
            if "/products/" in path:
                try:
                    resolved = resolve(path)
                    if resolved.url_name == "product_detail":
                        slug = resolved.kwargs.get("slug")
                        if slug:
                            product = Product.objects.filter(slug=slug, is_active=True).first()
                            if product:
                                # Deduplicate clicks from rapid reloads within 30s
                                recent_click = ProductClick.objects.filter(
                                    product=product,
                                    session_key=session_key,
                                    timestamp__gte=now - timedelta(seconds=30),
                                ).exists()
                                if not recent_click:
                                    ProductClick.objects.create(
                                        product=product,
                                        session_key=session_key,
                                        user=user,
                                        ip_address=ip,
                                    )
                                    Product.objects.filter(id=product.id).update(
                                        views_count=models.F("views_count") + 1
                                    )
                except Exception:
                    pass

        except Exception:
            # Never break user requests due to analytics recording errors
            pass

        response = self.get_response(request)
        return response
