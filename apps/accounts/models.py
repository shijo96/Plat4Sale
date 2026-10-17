from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Email Address")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Phone Number")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    class Meta:
        db_table = "accounts_user"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.get_full_name() or self.username


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=120, verbose_name="Full Name")
    phone = models.CharField(max_length=20, verbose_name="Phone Number")
    address_line1 = models.CharField(max_length=255, verbose_name="Flat, House no., Building, Apartment")
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name="Area, Street, Sector, Village")
    landmark = models.CharField(max_length=150, blank=True, verbose_name="Landmark (Optional)")
    city = models.CharField(max_length=100, verbose_name="Town / City")
    state = models.CharField(max_length=100, verbose_name="State")
    pincode = models.CharField(max_length=10, verbose_name="Pincode / Postal Code")
    is_default = models.BooleanField(default=False, verbose_name="Default Address")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]
        verbose_name = "Address"
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.pincode}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other addresses of this user to not default
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
