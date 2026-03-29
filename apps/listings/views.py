from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.listings.models import Listing
from apps.listings.permissions import IsOwnerOrReadOnly, CanMakeOffer
from apps.listings.serializers import ListingSerializer, OfferSerializer


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer

    def get_permissions(self):
        if self.action == 'offers':
            return [IsAuthenticated(), CanMakeOffer()]
        return [IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_queryset(self):
        qs = Listing.objects.filter(
            Q(seller=self.request.user) | Q(status='active')
        ).select_related('seller', 'category')
        return qs

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


