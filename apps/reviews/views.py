from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.catalog.models import Product
from .models import Review
from .forms import ReviewForm


@login_required
def add_review_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)

    existing_review = Review.objects.filter(user=request.user, product=product).first()

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.is_approved = True  # Can be auto-approved, moderated in admin panel
            review.save()
            messages.success(request, f"Thank you! Your review for '{product.name}' has been submitted.")
            return redirect("catalog:product_detail", slug=product.slug)
    else:
        form = ReviewForm(instance=existing_review)

    return render(request, "store/add_review.html", {
        "form": form,
        "product": product,
        "existing_review": existing_review,
    })
