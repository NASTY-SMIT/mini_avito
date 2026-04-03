from django.urls import path

from .views import RegisterView, MeView
from ..listings.views import MeFavoritesView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path('me/favorites/', MeFavoritesView.as_view(), name='me-favorites'),
]