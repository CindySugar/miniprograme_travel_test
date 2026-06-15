from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TravelViewSet

router = DefaultRouter()
router.register(r"travels", TravelViewSet, basename="travel")

urlpatterns = [
    path("", include(router.urls)),
]
