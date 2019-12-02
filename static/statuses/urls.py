from django.urls import path

from static.statuses import views

app_name = "statuses"

urlpatterns = [
    path("", views.StatusesAsList.as_view(), name="case_statuses"),
    path("properties/<str:status>/", views.StatusProperties.as_view(), name="case_status_properties"),
]
