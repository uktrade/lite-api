from django.urls import path

from licences import views

app_name = "licences"

urlpatterns = [
    path("", views.Licences.as_view(), name="licences"),
    path("<uuid:pk>/", views.ViewLicence.as_view(), name="licence"),
]
