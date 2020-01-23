from django.urls import path, include

from cases.views import views, activity, case_notes
from cases.views.search import views as search_views

app_name = "cases"

urlpatterns = [
    path("", search_views.CasesSearchView.as_view(), name="search"),
    path("destinations/<str:pk>/", views.Destination.as_view(), name="destination"),
    path("<uuid:pk>/", views.CaseDetail.as_view(), name="case"),
    path("<uuid:pk>/case-notes/", case_notes.CaseNoteList.as_view(), name="case_notes"),
    path("<uuid:pk>/case-officer/", views.CaseOfficer.as_view(), name="case_officer"),
    path("<uuid:pk>/activity/", activity.Activity.as_view(), name="activity"),
    path("<uuid:pk>/documents/", views.CaseDocuments.as_view(), name="documents"),
    path("<uuid:pk>/documents/<str:s3_key>/", views.CaseDocumentDetail.as_view(), name="document",),
    path(
        "<uuid:case_pk>/documents/<uuid:document_pk>/download/",
        views.ExporterCaseDocumentDownload.as_view(),
        name="document",
    ),
    path("<uuid:pk>/user-advice/", views.CaseAdvice.as_view(), name="case_advice"),
    path("<uuid:pk>/team-advice/", views.CaseTeamAdvice.as_view(), name="case_team_advice",),
    path("<uuid:pk>/view-team-advice/<uuid:team_pk>/", views.ViewTeamAdvice.as_view(), name="view_team_advice",),
    path("<uuid:pk>/final-advice/", views.CaseFinalAdvice.as_view(), name="case_final_advice",),
    path("<uuid:pk>/view-final-advice/", views.ViewFinalAdvice.as_view(), name="view_final_advice",),
    path(
        "<uuid:pk>/goods-countries-decisions/",
        views.GoodsCountriesDecisions.as_view(),
        name="goods_countries_decisions",
    ),
    path("<uuid:pk>/ecju-queries/", views.CaseEcjuQueries.as_view(), name="case_ecju_queries",),
    path("<uuid:pk>/ecju-queries/<uuid:ecju_pk>/", views.EcjuQueryDetail.as_view(), name="case_ecju_query",),
    path("<uuid:pk>/generated-documents/", include("cases.generated_documents.urls")),
]
