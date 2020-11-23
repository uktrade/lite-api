from django.urls import path, include

urlpatterns = [
    path("application/", include("api.search.application.urls")),
    path("product/", include("api.search.product.urls")),
]
