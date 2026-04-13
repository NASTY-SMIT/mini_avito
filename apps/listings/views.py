from django.db.models import Q
from django.db import transaction
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Prefetch

from apps.core.enums import OfferStatus, Status
from apps.listings.models import Listing, Offer, Favorite
from apps.listings.permissions import IsOwnerOrReadOnly, CanMakeOffer
from apps.listings.serializers import OfferSerializer, ListingListSerializer, ListingDetailSerializer, \
    FavoriteSerializer
from apps.listings.services import ListingService, FavoriteService, OfferService


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['title']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ListingDetailSerializer
        return ListingListSerializer

    def get_permissions(self):
        if self.action == 'offers':
            return [IsAuthenticated(), CanMakeOffer()]
        if self.action == 'favorite':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_queryset(self):
        qs = Listing.objects.filter(
            Q(seller=self.request.user) | Q(status='active')
        ).select_related('seller', 'category')

        if self.action == 'retrieve':
            qs = qs.prefetch_related(
                Prefetch('offers', queryset=Offer.objects.select_related('buyer'))
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    def perform_destroy(self, instance):
        ListingService.archive_listing(instance)

    @action(detail=True, methods=['post'], url_path='offers')
    def offers(self, request, pk=None):
        listing = self.get_object()
        serializer = OfferSerializer(
            data=request.data,
            context={'request': request, 'listing': listing}
        )
        serializer.is_valid(raise_exception=True)
        offer = OfferService.create_offer(
            listing=listing,
            buyer=request.user,
            proposed_price=serializer.validated_data['proposed_price']
        )

        return Response(
            OfferSerializer(offer).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        listing = self.get_object()
        user = request.user
        if request.method == 'POST':
            favorite, created = FavoriteService.add(user, listing)
            if not created:
                return Response({"detail": "Уже в избранном"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": "Добавлено в избранное"}, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted_count = FavoriteService.remove(user, listing)
            if deleted_count == 0:
                return Response({"detail": "Не найдено в избранном"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"detail": "Удалено из избранного"}, status=status.HTTP_204_NO_CONTENT)


class OfferViewSet(viewsets.ModelViewSet):
    queryset = Offer.objects.select_related('listing', 'buyer', 'listing__seller')
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Offer.objects.none()
        user = self.request.user
        return Offer.objects.filter(
            Q(buyer=user) | Q(listing__seller=user)
        ).select_related('listing', 'buyer', 'listing__seller')

    def update(self, request, *args, **kwargs):
        offer_id = kwargs.get("pk")
        new_status = request.data.get("status")

        if new_status == OfferStatus.ACCEPTED:
            offer = OfferService.accept_offer(offer_id, request.user)
        elif new_status == OfferStatus.REJECTED:
            offer = OfferService.reject_offer(offer_id, request.user)
        else:
            raise ValidationError("Неверный статус")

        return Response(self.get_serializer(offer).data)


class MeFavoritesView(generics.ListAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('listing')


