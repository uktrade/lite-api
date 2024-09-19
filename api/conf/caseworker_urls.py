from django.urls import path, include

urlpatterns = [
    path("applications/", include("api.applications.caseworker.urls")),
    path("organisations/", include("api.organisations.caseworker.urls")),
]
