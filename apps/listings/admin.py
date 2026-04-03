from django.contrib import admin

from apps.listings.models import Listing, Offer


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    pass

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    pass
