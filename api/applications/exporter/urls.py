from django.urls import path

from api.applications.exporter.views import applications

app_name = "exporter_applications"

urlpatterns = [
    path("<uuid:pk>/status/", applications.ApplicationChangeStatus.as_view(), name="change_status"),
]