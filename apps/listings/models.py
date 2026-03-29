from django.db import models
from django.contrib.auth import get_user_model
from apps.categories.models import Category
from apps.core.enums import Status, OfferStatus

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


class Offer(models.Model):
    listing = models.ForeignKey(
        'Listing',
        on_delete=models.CASCADE,
        related_name='offers'
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    proposed_price = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=OfferStatus,
        default=OfferStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ['listing', 'buyer']

    def __str__(self):
        return f"Offer {self.proposed_price} by {self.buyer.username} on {self.listing.title}"
