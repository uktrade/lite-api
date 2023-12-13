from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.search.product import views


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"search", views.ProductDocumentView, basename="product_search")


urlpatterns = [
    path("", include(router.urls)),
    path("suggest/", views.ProductSuggestDocumentView.as_view(), name="product_suggest"),
]
