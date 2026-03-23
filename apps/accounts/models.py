from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    # Можно добавить позже:
    # phone = models.CharField(max_length=20, blank=True)
    # avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    # bio = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    # Очень удобно — profile всегда будет создаваться автоматически при создании пользователя
    @classmethod
    def create_for_user(cls, user):
        return cls.objects.create(user=user)
