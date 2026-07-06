from django.db import models
from django.contrib.auth.models import User
from PIL import Image
import os


class Profile(models.Model):

    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'

    class MaritalStatus(models.TextChoices):
        SINGLE = 'single', 'Single'
        MARRIED = 'married', 'Married'
        DIVORCED = 'divorced', 'Divorced'
        WIDOWED = 'widowed', 'Widowed'

    # 🔗 RELATION
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # 👤 PERSONAL INFO (Do NOT duplicate first_name, last_name)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    marital_status = models.CharField(max_length=10, choices=MaritalStatus.choices, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # 📍 LOCATION
    address = models.CharField(max_length=255, blank=True)

    # 🖼️ PROFILE IMAGE
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        default='default.jpg',
        blank=True
    )

    # 🕒 SYSTEM FIELDS
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.profile_picture or self.profile_picture.name == 'default.jpg':
            return

        try:
            img_path = self.profile_picture.path
        except (NotImplementedError, ValueError):
            return

        if os.path.exists(img_path):
            img = Image.open(img_path)

            if img.height > 300 or img.width > 300:
                img.thumbnail((300, 300))
                img.save(img_path)