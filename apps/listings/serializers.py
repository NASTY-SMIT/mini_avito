from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.categories.models import Category
from apps.categories.serializers import CategorySerializer
from apps.listings.models import Listing


class ListingSerializer(serializers.ModelSerializer):
    seller_username = serializers.ReadOnlyField(source='seller.username')
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),
        write_only=False,
    )


    class Meta:
        model = Listing
        fields = ("id", "seller_username", "category", "title", "description", "price", "status")

    def validate_price(self, value):
        if not value:
            raise serializers.ValidationError("Цена обязательна")
        try:
            float(value)
        except ValueError:
            raise serializers.ValidationError("Цена должна быть числом")
        if len(str(value)) > 20:
            raise serializers.ValidationError("Слишком длинная цена")
        return value
