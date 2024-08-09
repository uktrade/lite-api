from django.urls import path, include

urlpatterns = [
    path("applications/", include("api.applications.exporter.urls")),
]
