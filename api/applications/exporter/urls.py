from django.urls import path

from api.applications.exporter.views import applications

app_name = "exporter_applications"

urlpatterns = [
    path("<uuid:pk>/status/", applications.ApplicationChangeStatus.as_view(), name="change_status"),
    path("<uuid:pk>/history/", applications.ApplicationHistory.as_view(), name="history"),
    path("<uuid:pk>/documents/", applications.ApplicationDocuments.as_view(), name="documents"),
]
