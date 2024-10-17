from django.urls import path, include


urlpatterns = [
    path("data-workspace/", include("api.data_workspace.urls")),
]
