from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with staff/admin credentials to access the admin panel.")
            return redirect(f"/accounts/login/?next={request.path}")
        if not request.user.is_staff:
            messages.error(request, "Access restricted: Staff privileges required to view the management dashboard.")
            return redirect("catalog:home")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
