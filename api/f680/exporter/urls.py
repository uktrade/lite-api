from django.urls import path

from api.f680.exporter.views import F680ApplicationViewSet  # /PS-IGNORE

app_name = "exporter_f680"

urlpatterns = [
    path(
        "application/",
        F680ApplicationViewSet.as_view({"get": "list", "post": "create"}),
        name="applications",
    ),
    path(
        "application/<uuid:f680_application_id>/",
        F680ApplicationViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="application",
    ),
    path(
        "application/<uuid:f680_application_id>/submit/",
        F680ApplicationViewSet.as_view({"post": "submit"}),
        name="application_submit",
    ),
]
