import django_filters
from django.db.models import DecimalField
from django.db.models.functions import Cast

from .models import Offer


class OfferFilter(django_filters.FilterSet):
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
        ),
        method='order_by_price'
    )

    class Meta:
        model = Offer
        fields = []

    def order_by_price(self, queryset, name, value):
        """Сортировка по предложенной цене"""
        if not value:
            return queryset
        annotated_qs = queryset.annotate(
            price_decimal=Cast('proposed_price', DecimalField(max_digits=12, decimal_places=2))
        )
        for param in value:
            if param == 'price':
                annotated_qs = annotated_qs.order_by('price_decimal')
        return annotated_qs
