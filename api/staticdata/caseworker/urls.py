from django.urls import path, include

app_name = "caseworker_staticdata"

urlpatterns = [
    path("control-list-entries/", include("api.staticdata.caseworker.control_list_entries.urls")),
]
