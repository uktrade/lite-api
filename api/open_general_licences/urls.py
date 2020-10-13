from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.open_general_licences import views

app_name = "open_general_licences"

router = DefaultRouter()
router.register("", views.OpenGeneralLicenceListDW, basename="ogl-dw")


urlpatterns = [
    path("", views.OpenGeneralLicenceList.as_view(), name="list"),
    path("<uuid:pk>/", views.OpenGeneralLicenceDetail.as_view(), name="detail"),
    path("<uuid:pk>/activity/", views.OpenGeneralLicenceActivityView.as_view(), name="activity"),
    path("dw", include(router.urls)),
]
