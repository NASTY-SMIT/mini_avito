from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core.enums import OfferStatus, Status
from apps.listings.models import Listing, Offer


class OfferService:
    """Сервис для работы с предложениями цены"""

    @staticmethod
    def create_offer(listing: Listing, buyer, proposed_price: str):
        """Создать предложение цены"""
        offer = Offer.objects.create(
            listing=listing,
            buyer=buyer,
            proposed_price=proposed_price
        )
        return offer

    @staticmethod
    @transaction.atomic
    def accept_offer(offer_id: int, seller):
        """Принять предложение"""
        offer = Offer.objects.select_related('listing').select_for_update().get(id=offer_id)
        listing = Listing.objects.select_for_update().get(id=offer.listing_id)

        if listing.seller != seller:
            raise PermissionDenied("Только продавец может принимать предложение")

        if listing.status == Status.SOLD:
            raise ValidationError("Объявление уже продано")

        if offer.status != OfferStatus.PENDING:
            raise ValidationError("Предложение уже обработано")

        # Принимаем предложение
        offer.status = OfferStatus.ACCEPTED
        offer.save(update_fields=['status'])

        # Объявление становится проданным
        listing.status = Status.SOLD
        listing.save(update_fields=['status'])

        # Отклоняем все остальные предложения
        Offer.objects.filter(
            listing=listing,
            status=OfferStatus.PENDING
        ).exclude(id=offer.id).update(status=OfferStatus.REJECTED)

        return offer

    @staticmethod
    @transaction.atomic
    def reject_offer(offer_id: int, seller):
        """Отклонить предложение"""
        offer = Offer.objects.select_related('listing').get(id=offer_id)

        if offer.listing.seller != seller:
            raise PermissionDenied("Только продавец может отклонять предложение")

        if offer.status != OfferStatus.PENDING:
            raise ValidationError("Предложение уже обработано")

        offer.status = OfferStatus.REJECTED
        offer.save(update_fields=['status'])

        return offer