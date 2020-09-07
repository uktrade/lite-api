from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.search.application import views


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"application_search", views.ApplicationDocumentView, basename="application_search")


urlpatterns = [
    path("", include(router.urls)),
    path("suggest/", views.ApplicationSuggestDocumentView.as_view(), name="application_suggest"),
]
