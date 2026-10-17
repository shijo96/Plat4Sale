from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "title", "comment"]
        widgets = {
            "rating": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "What's most important to know?"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Write your full review here..."}),
        }
