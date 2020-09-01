from django.urls import path, include

urlpatterns = [
    path("application/", include("api.search.application.urls")),
]
