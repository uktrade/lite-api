from django.urls import path, include

app_name = "exporter_staticdata"

urlpatterns = [
    path("control-list-entries/", include("api.staticdata.exporter.control_list_entries.urls")),
]
