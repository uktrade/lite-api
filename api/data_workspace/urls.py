from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.data_workspace import license_views

app_name = "data_workspace"

router = DefaultRouter()
router.register("v1/licences", license_views.LicencesListDW, basename="dw-licences")
router.register("v1/ogl", license_views.OpenGeneralLicenceListDW, basename="dw-ogl")

urlpatterns = [
    path("", include(router.urls)),
]
