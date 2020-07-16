from django.urls import path, include

from cases.views import views, case_notes, licences, case_actions
from cases.views.search import views as search_views
from cases.views.search.activity import CaseActivityView, CaseActivityFiltersView
from cases.enforcement_check import views as enforcement_check

app_name = "cases"

urlpatterns = [
    path("", search_views.CasesSearchView.as_view(), name="search"),
    path(
        "enforcement-check/<uuid:queue_pk>/", enforcement_check.EnforcementCheckView.as_view(), name="enforcement_check"
    ),
    path("destinations/<str:pk>/", views.Destination.as_view(), name="destination"),
    path("<uuid:pk>/", views.CaseDetail.as_view(), name="case"),
    path("<uuid:pk>/queues/", views.SetQueues.as_view(), name="queues"),
    path("<uuid:pk>/case-notes/", case_notes.CaseNoteList.as_view(), name="case_notes"),
    path("<uuid:pk>/case-officer/", views.CaseOfficer.as_view(), name="case_officer"),
    path("<uuid:pk>/activity/", CaseActivityView.as_view(), name="activity"),
    path("<uuid:pk>/activity/filters/", CaseActivityFiltersView.as_view(), name="activity_filters"),
    path("<uuid:pk>/additional-contacts/", views.AdditionalContacts.as_view(), name="additional_contacts"),
    path("<uuid:pk>/applicant/", views.CaseApplicant.as_view(), name="case_applicant"),
    path("<uuid:pk>/documents/", views.CaseDocuments.as_view(), name="documents"),
    path("<uuid:pk>/documents/<str:s3_key>/", views.CaseDocumentDetail.as_view(), name="document",),
    path(
        "<uuid:case_pk>/documents/<uuid:document_pk>/download/",
        views.ExporterCaseDocumentDownload.as_view(),
        name="document_download",
    ),
    path("<uuid:pk>/user-advice/", views.UserAdvice.as_view(), name="user_advice"),
    path("<uuid:pk>/team-advice/", views.TeamAdviceView.as_view(), name="team_advice",),
    path("<uuid:pk>/final-advice/", views.FinalAdvice.as_view(), name="case_final_advice",),
    path("<uuid:pk>/final-advice-documents/", views.FinalAdviceDocuments.as_view(), name="final_advice_documents",),
    path(
        "<uuid:pk>/goods-countries-decisions/",
        views.GoodsCountriesDecisions.as_view(),
        name="goods_countries_decisions",
    ),
    path("<uuid:pk>/open-licence-decision/", views.OpenLicenceDecision.as_view(), name="open_licence_decision",),
    path("<uuid:pk>/ecju-queries/", views.ECJUQueries.as_view(), name="case_ecju_queries",),
    path("<uuid:pk>/ecju-queries/<uuid:ecju_pk>/", views.EcjuQueryDetail.as_view(), name="case_ecju_query",),
    path("<uuid:pk>/generated-documents/", include("cases.generated_documents.urls")),
    path("<uuid:pk>/finalise/", views.FinaliseView.as_view(), name="finalise"),
    path("<uuid:pk>/licences/", licences.LicencesView.as_view(), name="licences"),
    path("<uuid:pk>/assigned-queues/", case_actions.AssignedQueues.as_view(), name="assigned_queues"),
    path("<uuid:pk>/reissue-ogel/", case_actions.OpenGeneralLicenceReissue.as_view(), name="reissue_ogel"),
    path("<uuid:pk>/rerun-routing-rules/", case_actions.RerunRoutingRules.as_view(), name="rerun_routing_rules"),
    path("<uuid:pk>/review-date/", views.NextReviewDate.as_view(), name="review_date"),
]
