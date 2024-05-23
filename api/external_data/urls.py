from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.external_data import views

app_name = "external_data"

router = DefaultRouter()
router.register("denial", views.DenialViewSet, basename="denial")
router.register("sanction", views.SanctionViewSet, basename="sanction")


urlpatterns = [
    path("", include(router.urls)),
    path("sanction-search", views.SanctionSearchView.as_view(), name="sanction-search"),
    path("denial-search/", views.DenialSearchView.as_view(), name="denial_search"),
]
