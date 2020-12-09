from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.search.product import views


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"search", views.ProductDocumentView, basename="product_search")


urlpatterns = [
    path("", include(router.urls)),
    path("suggest/", views.ProductSuggestDocumentView.as_view(), name="product_suggest"),
    path("spire/<str:pk>/comment/", views.CommentView.as_view(), name="retrieve_spire_product_comment"),
    path("lite/<uuid:pk>/comment/", views.CommentView.as_view(), name="retrieve_lite_product_comment"),
    path("spire/<str:pk>/", views.RetrieveSpireProductView.as_view(), name="retrieve_spire_product"),
    path("lite/<uuid:pk>/", views.RetrieveLiteProductView.as_view(), name="retrieve_lite_product"),
]
