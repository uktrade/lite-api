from django.urls import path

from api.applications.caseworker.views import applications

app_name = "caseworker_applications"

urlpatterns = [
    path("<uuid:pk>/status/", applications.ApplicationChangeStatus.as_view(), name="change_status"),
    path("<uuid:pk>/supporting-document/", applications.ApplicationDocumentView.as_view(), name="document"),
]
