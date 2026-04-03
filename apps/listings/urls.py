from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, OfferViewSet

router = DefaultRouter()
router.register('', ListingViewSet, basename='listing')
router.register('offers', OfferViewSet)

urlpatterns = router.urls