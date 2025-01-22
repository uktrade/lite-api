from django.urls import path

from api.f680.exporter.views import F680ApplicationView  # /PS-IGNORE


app_name = "exporter_f680"  # /PS-IGNORE

urlpatterns = [
    path("", F680ApplicationView.as_view(), name="application"),  # /PS-IGNORE
]
