from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.search.goa import views


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"goa_search", views.GoodOnApplicationDocumentView, basename="goa_search")

urlpatterns = [
    path("", include(router.urls))
]
