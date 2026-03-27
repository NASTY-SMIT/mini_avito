from django.db import models
from django.contrib.auth import get_user_model
from apps.categories.models import Category
from apps.core.enums import Status


User = get_user_model()


class Listing(models.Model):
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="listings",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="listings",
    )
    title = models.CharField(verbose_name="Listing Name", max_length=300)
    price = models.CharField(verbose_name="Listing Price", max_length=100)
    status = models.CharField(verbose_name="Listing Status", choices=Status, max_length=100, default=Status.ACTIVE)
    description = models.TextField(verbose_name="Listing Description", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Listing of {self.title}"

    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        ordering = ['-created_at']
