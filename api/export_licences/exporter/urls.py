from django.urls import path

from api.export_licences.exporter.views import ExportLicenceApplicationViewSet

app_name = "exporter_export_licences"

urlpatterns = [
    path(
        "application/",
        ExportLicenceApplicationViewSet.as_view({"post": "create"}),
        name="applications",
    ),
]
