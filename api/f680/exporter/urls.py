from django.urls import path

from api.f680.exporter.views import (
    F680ApplicationView,
    F680ApplicationsView,  # /PS-IGNORE
)


app_name = "exporter_f680"  # /PS-IGNORE

urlpatterns = [
    path("", F680ApplicationsView.as_view(), name="applications"),  # /PS-IGNORE
    path("<uuid:pk>/", F680ApplicationView.as_view(), name="application"),
]
