from django.urls import path

from audit_trail.streams import views

app_name = "audit_trail"

urlpatterns = [
    path("streams/<int:timestamp>", views.streams, name="streams"),
]
