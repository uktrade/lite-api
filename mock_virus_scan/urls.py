from django.urls import path
from mock_virus_scan import views

app_name = "mock_virus_scan"

urlpatterns = [
    path("scan", views.Scan.as_view(), name="scan"),
]
