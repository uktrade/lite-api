from django.urls import path

from api.f680.exporter.views import F680ApplicationViewSet  # /PS-IGNORE

app_name = "exporter_f680"

urlpatterns = [
    path(
        "application/",
        F680ApplicationViewSet.as_view({"get": "list", "post": "create"}),  # /PS-IGNORE
        name="applications",
    ),
    path(
        "application/<uuid:f680_application_id>/",
        F680ApplicationViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),  # /PS-IGNORE
        name="application",
    ),
]
