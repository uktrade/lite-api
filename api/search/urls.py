from django.urls import path, include

urlpatterns = [
    path("goa/", include("api.search.goa.urls")),
]
