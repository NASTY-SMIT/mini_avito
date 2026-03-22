from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.categories.serializers import CategorySerializer
from apps.listings.models import Listing


class ListingSerializer(serializers.ModelSerializer):
    seller = UserSerializer()
    category = CategorySerializer()


    class Meta:
        model = Listing
        fields = ("id", "seller", "category", "title", "description", "price", "status")
        extra_kwargs = {"seller": {"read_only": True},
                        "id": {"read_only": True},}

    def validate_price(self, data):
        if len(data) > 20:
            raise serializers.ValidationError({"price": "Price must be less than or equal to 20"})
