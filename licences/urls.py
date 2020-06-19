from django.urls import path

from licences.views import main, open_general_licences

app_name = "licences"

urlpatterns = [
    path("", main.Licences.as_view(), name="licences"),
    path("<uuid:pk>/", main.ViewLicence.as_view(), name="licence"),
    path("nlrs/", main.NLRs.as_view(), name="nlrs"),
    path("hmrc-integration/", main.NLRs.as_view(), name="nlrs"),
    path("open-general-licences/", open_general_licences.Create.as_view(), name="open_general_licences"),
]
