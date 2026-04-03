from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.categories.models import Category
from apps.categories.serializers import CategorySerializer
from apps.core.enums import OfferStatus, Status
from apps.listings.models import Listing, Offer, Favorite


class ListingListSerializer(serializers.ModelSerializer):
    seller_username = serializers.ReadOnlyField(source='seller.username')
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),
    )

    class Meta:
        model = Listing
        fields = ("id", "seller_username", "category", "title", "price", "status")


class ListingDetailSerializer(ListingListSerializer):
    offers = serializers.SerializerMethodField()

    class Meta(ListingListSerializer.Meta):  # наследуем Meta
        fields = ListingListSerializer.Meta.fields + ('offers',)

    def get_offers(self, obj):
        request = self.context.get("request")
        if request and obj.seller == request.user:
            return OfferSerializer(obj.offers.all(), many=True).data
        return []



class OfferSerializer(serializers.ModelSerializer):
    buyer_username = serializers.ReadOnlyField(source='buyer.username')
    listing = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Offer
        fields = ['id', 'buyer_username', 'listing', 'proposed_price', 'status', 'created_at']

    def validate(self, attrs):
        listing = self.context['listing']
        user = self.context['request'].user

        if listing.seller == user:
            raise serializers.ValidationError("Нельзя делать предложение на своё объявление")
        if listing.status in [Status.SOLD.value, Status.ARCHIVED.value]:
            raise serializers.ValidationError("Объявление уже продано или в архиве")
        return attrs


class FavoriteSerializer(serializers.ModelSerializer):
    listing = serializers.PrimaryKeyRelatedField(read_only=True)
    listing_title = serializers.ReadOnlyField(source="listing.title")
    listing_price = serializers.ReadOnlyField(source="listing.price")
    listing_status = serializers.ReadOnlyField(source="listing.status")

    class Meta:
        model = Favorite
        fields = ['id', 'listing', 'listing_title', 'listing_price', 'listing_status', 'created_at']
