from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.data_workspace import application_views
from api.data_workspace import license_views

app_name = "data_workspace"

router = DefaultRouter()
router.register(
    "v1/standard-applications", application_views.StandardApplicationListView, basename="dw-standard-applications"
)
router.register(
    "v1/good-on-applications", application_views.GoodOnApplicationListView, basename="dw-good-on-applications"
)
router.register(
    "v1/party-on-applications", application_views.PartyOnApplicationListView, basename="dw-party-on-applications"
)
router.register("v1/licences", license_views.LicencesListDW, basename="dw-licences")
router.register("v1/ogl", license_views.OpenGeneralLicenceListDW, basename="dw-ogl")

urlpatterns = [
    path("", include(router.urls)),
]
