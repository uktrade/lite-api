from django.urls import path

from compliance import views

app_name = "compliance"

# urls will be required in future compliance stories, conf has already been set up
urlpatterns = [
    path("<uuid:pk>/licences/", views.LicenceList.as_view(), name="licences",),
    path("<uuid:pk>/status/", views.ComplianceManageStatus.as_view(), name="manage_status",),
    path("case/<uuid:pk>/", views.ComplianceCaseId.as_view(), name="compliance_case_id"),
    path("open-licence-returns/", views.OpenLicenceReturnsView.as_view(), name="open_licence_returns"),
    path(
        "open-licence-returns/<uuid:pk>/",
        views.OpenLicenceReturnDownloadView.as_view(),
        name="open_licence_return_download",
    ),
]
