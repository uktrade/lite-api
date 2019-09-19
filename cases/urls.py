from django.urls import path

from cases.views import views, activity, case_notes

app_name = 'cases'

urlpatterns = [
    # ex: /cases/<uuid:pk>/
    path('<uuid:pk>/', views.CaseDetail.as_view(), name='case'),
    # ex: /cases/<uuid:pk>/case-notes/
    path('<uuid:pk>/case-notes/', case_notes.CaseNoteList.as_view(), name='case_notes'),
    # ex: /cases/<uuid:pk>/activity/
    path('<uuid:pk>/activity/', activity.Activity.as_view(), name='activity'),
    # ex: /cases/<uuid:pk>/documents/
    path('<uuid:pk>/documents/', views.CaseDocuments.as_view(), name='documents'),
    # ex: /cases/<uuid:pk>/documents/<uuid:file_pk>/
    path('<uuid:pk>/documents/<str:s3_key>/', views.CaseDocumentDetail.as_view(), name='document'),
    # ex: /cases/<uuid:pk>/advice/
    path('<uuid:pk>/user-advice/', views.CaseAdvice.as_view(), name='case_advice'),
    # ex: /cases/<uuid:pk>/team-advice/
    path('<uuid:pk>/team-advice/', views.CaseTeamAdvice.as_view(), name='case_team_advice'),
    # ex: /cases/<uuid:pk>/team-advice/<uuid:team_pk>/
    path('<uuid:pk>/view-team-advice/<uuid:team_pk>/', views.ViewTeamAdvice.as_view(), name='view_team_advice'),
    # ex: /cases/<uuid:pk>/final-advice/
    path('<uuid:pk>/final-advice/', views.CaseFinalAdvice.as_view(), name='case_final_advice'),
    # ex: /cases/<uuid:pk>/view-final-advice/
    path('<uuid:pk>/view-final-advice/', views.ViewFinalAdvice.as_view(), name='view_final_advice'),
    # ex: /cases/<uuid:pk>/ecju-queries/
    path('<uuid:pk>/ecju-queries/', views.CaseEcjuQueries.as_view(), name='case_ecju_queries'),
    # ex: /cases/<uuid:pk>/ecju-queries/<uuid:ecju_pk>/
    path('<uuid:pk>/ecju-queries/<uuid:ecju_pk>/', views.EcjuQueryDetail.as_view(), name='case_ecju_query'),
]
