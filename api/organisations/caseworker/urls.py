from django.urls import path

from api.organisations.caseworker.views import users

app_name = "caseworker_organisations"

urlpatterns = [
    path("<uuid:org_pk>/exporter-users/", users.CreateExporterUser.as_view(), name="exporter_user"),
]
