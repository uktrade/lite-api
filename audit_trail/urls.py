from django.urls import path

from audit_trail import views

app_name = "audit_trail"

urlpatterns = [
    path("streams/<int:n>", views.streams, name="flags"),
]
