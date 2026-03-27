from rest_framework.routers import DefaultRouter
from .views import ListingViewSet

router = DefaultRouter()
router.register('', ListingViewSet, basename='listing')          # ← basename не нужен, если есть queryset

urlpatterns = router.urls