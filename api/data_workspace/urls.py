from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.data_workspace import views

app_name = "data_workspace"

router = DefaultRouter()
router.register("v1/licences", views.LicencesListDW, basename="dw-licences")
router.register("v1/ogl", views.OpenGeneralLicenceListDW, basename="dw-ogl")

urlpatterns = [
    path("", include(router.urls)),
]
