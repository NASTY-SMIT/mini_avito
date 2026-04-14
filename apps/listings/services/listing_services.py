from apps.core.enums import Status
from apps.listings.models import Listing


class ListingService:
    """Сервис для работы с объявлениями"""

    @staticmethod
    def archive_listing(listing: Listing) -> None:
        """Мягкое удаление объявления"""
        listing.status = Status.ARCHIVED
        listing.save(update_fields=['status'])
