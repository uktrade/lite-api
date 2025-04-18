from django.urls import path

from api.compliance import views

app_name = "compliance"

urlpatterns = [
    path("exporter/", views.ExporterComplianceListSerializer.as_view(), name="exporter_site_list"),
    path("exporter/<uuid:pk>/", views.ExporterComplianceSiteDetailView.as_view(), name="exporter_site_detail"),
    path("exporter/<uuid:pk>/visits/", views.ExporterVisitList.as_view(), name="exporter_visit_case_list"),
    path("exporter/visits/<uuid:pk>/", views.ExporterVisitDetail.as_view(), name="exporter_visit_case_detail"),
    path(
        "<uuid:pk>/licences/",
        views.LicenceList.as_view(),
        name="licences",
    ),
    path(
        "site/<uuid:pk>/visit/",
        views.ComplianceSiteVisits.as_view(),
        name="compliance_visit",
    ),
    path("case/<uuid:pk>/", views.ComplianceCaseId.as_view(), name="compliance_case_id"),
    path("visit/<uuid:pk>/", views.ComplianceVisitCaseView.as_view(), name="visit_case"),
    path("visit/<uuid:pk>/people-present/", views.ComplianceVisitPeoplePresentView.as_view(), name="people_present"),
    path(
        "visit/people-present/<uuid:pk>/",
        views.ComplianceVisitPersonPresentView.as_view(),
        name="person_present",
    ),
]
