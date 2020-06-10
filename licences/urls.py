from django.urls import path

from licences.views import main, open_general_licences

app_name = "licences"

urlpatterns = [
    path("", main.Licences.as_view(), name="licences"),
    path("<uuid:pk>/", main.ViewLicence.as_view(), name="licence"),
    path("open-general-licences/", open_general_licences.ListCreate.as_view(), name="open-general-licences"),
    path("open-general-licences/<uuid:pk>/", open_general_licences.RetrieveUpdate.as_view(), name="open-general-licence"),
]
