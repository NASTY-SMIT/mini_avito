from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.listings.models import Listing
from apps.listings.permissions import IsOwnerOrReadOnly
from apps.listings.serializers import ListingSerializer


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = Listing.objects.filter(
            Q(seller=self.request.user) | Q(status='active')
        ).select_related('seller', 'category')
        return qs

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)


