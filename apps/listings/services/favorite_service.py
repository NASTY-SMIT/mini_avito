from apps.listings.models import Listing, Favorite


class FavoriteService:
    """Сервис для работы с избранным"""

    @staticmethod
    def add(user, listing: Listing):
        """Добавить объявление в избранное"""
        favorite, created = Favorite.objects.get_or_create(user=user, listing=listing)
        return favorite, created

    @staticmethod
    def remove(user, listing: Listing) -> int:
        """Удалить объявление из избранного"""
        deleted_count, _ = Favorite.objects.filter(user=user, listing=listing).delete()
        return deleted_count