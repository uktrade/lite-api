from django.urls import path

from compliance import views

app_name = "compliance"

# urls will be required in future compliance stories, conf has already been set up
urlpatterns = [
    path("<uuid:pk>/licences/", views.LicenceList.as_view(), name="licences",),
    path("site/<uuid:pk>/status/", views.ComplianceSiteManageStatus.as_view(), name="manage_status",),
    path("site/<uuid:pk>/visit/", views.ComplianceSiteVisits.as_view(), name="manage_status",),
    path("case/<uuid:pk>/", views.ComplianceCaseId.as_view(), name="compliance_case_id"),
    path("visit/<uuid:pk>/", views.ComplianceVisitCaseView.as_view(), name="visit_update"),
    path("visit/<uuid:pk>/people-present/", views.ComplianceVisitPeoplePresentView.as_view(), name="people_present"),
    path("visit/people-present/<uuid:pk>/", views.ComplianceVisitPersonPresentView.as_view(), name="person_present",),
    path("visit/<uuid:pk>/status/", views.ComplianceSiteManageStatus.as_view(), name="manage_visit_status",),
    path("open-licence-returns/", views.OpenLicenceReturnsView.as_view(), name="open_licence_returns"),
    path(
        "open-licence-returns/<uuid:pk>/",
        views.OpenLicenceReturnDownloadView.as_view(),
        name="open_licence_return_download",
    ),
]
