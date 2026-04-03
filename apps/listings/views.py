from django.db.models import Q
from django.db import transaction
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.enums import OfferStatus, Status
from apps.listings.models import Listing, Offer, Favorite
from apps.listings.permissions import IsOwnerOrReadOnly, CanMakeOffer
from apps.listings.serializers import OfferSerializer, ListingListSerializer, ListingDetailSerializer, \
    FavoriteSerializer


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
        return [IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_queryset(self):
        return Listing.objects.filter(
            Q(seller=self.request.user) | Q(status='active')
        ).select_related('seller', 'category').prefetch_related('offers')

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    def perform_destroy(self, instance):
        instance.status = 'archived'
        instance.save()

    @action(detail=True, methods=['post'], url_path='offers')
    def offers(self, request, pk=None):
        listing = self.get_object()
        serializer = OfferSerializer(
            data=request.data,
            context={'request': request, 'listing': listing}
        )
        serializer.is_valid(raise_exception=True)
        offer = serializer.save(
            buyer=request.user,
            listing=listing
        )

        return Response(
            OfferSerializer(offer).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post', 'delete'], url_path='favorite', permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        listing = self.get_object()
        user = request.user
        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(user=user, listing=listing)
            if not created:
                return Response({"detail": "Уже в избранном"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": "Добавлено в избранное"}, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted_count, _ = Favorite.objects.filter(user=user, listing=listing).delete()
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
        user = request.user
        offer_id = kwargs.get("pk")

        with transaction.atomic():

            # ЛОЧИМ оффер + объявление
            offer = Offer.objects.select_related("listing").select_for_update().get(id=offer_id)

            listing = Listing.objects.select_for_update().get(id=offer.listing.id)

            if listing.seller != user:
                raise PermissionDenied("Только продавец может управлять офферами")

            if listing.status == Status.SOLD:
                raise ValidationError("Объявление уже продано")

            if offer.status != OfferStatus.PENDING:
                raise ValidationError("Оффер уже обработан")

            new_status = request.data.get("status")

            if new_status == OfferStatus.ACCEPTED:

                # принимаем оффер
                offer.status = OfferStatus.ACCEPTED
                offer.save()

                # объявление → sold
                listing.status = Status.SOLD
                listing.save()

                # остальные → rejected
                Offer.objects.filter(
                    listing=listing
                ).exclude(id=offer.id).update(status=OfferStatus.REJECTED)

            elif new_status == OfferStatus.REJECTED:
                offer.status = OfferStatus.REJECTED
                offer.save()
            else:
                raise ValidationError("Неверный статус")

        return Response(self.get_serializer(offer).data)


class MeFavoritesView(generics.ListAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('listing')


