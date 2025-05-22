from django.urls import path, include
from rest_framework.routers import DefaultRouter

from views import ApplicationManifestFeaturesViewSet

router = DefaultRouter()
router.register("manifest-settings", ApplicationManifestFeaturesViewSet, basename="manifest-settings")

urlpatterns = [
    path("", include(router.urls)),
]
