from django.urls import path

from api.applications.caseworker.views import applications

app_name = "caseworker_applications"

urlpatterns = [
    path("<uuid:pk>/status/", applications.ApplicationChangeStatus.as_view(), name="change_status"),
]
