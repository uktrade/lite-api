from django.urls import path

from api.dummy_health_check import views

app_name = "dummy_health_check"

urlpatterns = [
    path(
        "",
        views.HealthCheck.as_view(),
        name="healthcheck",
    ),
]
