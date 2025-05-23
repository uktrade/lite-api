from rest_framework.routers import DefaultRouter

from api.application_manifests.views import ApplicationManifestFeaturesViewSet

app_name = "application-manifest"  # Add this namespace

router = DefaultRouter()
router.register("", ApplicationManifestFeaturesViewSet, basename="manifest-feature")

urlpatterns = router.urls
