from django.urls import path

from api.licences.views import main, open_general_licences, hmrc_integration

app_name = "licences"

urlpatterns = [
    path("", main.Licences.as_view(), name="licences"),
    path("<uuid:pk>/", main.ViewLicence.as_view(), name="licence"),
    path("nlrs/", main.NLRs.as_view(), name="nlrs"),
    path(
        "hmrc-integration/force-mail-push/", hmrc_integration.force_mail_push, name="hmrc_integration_force_mail_push"
    ),
    path(
        "hmrc-integration/<uuid:pk>/",
        hmrc_integration.HMRCIntegrationRetrieveView.as_view(),
        name="hmrc_integration_retrieve",
    ),
    path("hmrc-integration/", hmrc_integration.HMRCIntegration.as_view(), name="hmrc_integration"),
    path("open-general-licences/", open_general_licences.Create.as_view(), name="open_general_licences"),
]
