from django.urls import path

from cases.views import views, activity

app_name = 'cases'

urlpatterns = [
    # ex: /cases/<uuid:pk>/
    path('<uuid:pk>/', views.CaseDetail.as_view(), name='case'),
    # ex: /cases/<uuid:pk>/case-notes/
    path('<uuid:pk>/case-notes/', views.CaseNoteList.as_view(), name='case_notes'),
    # ex: /cases/<uuid:pk>/activity/
    path('<uuid:pk>/activity/', activity.Activity.as_view(), name='activity'),
    # ex: /cases/<uuid:pk>/documents/
    path('<uuid:pk>/documents/', views.CaseDocuments.as_view(), name='documents'),
    # ex: /cases/<uuid:pk>/documents/<uuid:file_pk>/
    path('<uuid:pk>/documents/<str:s3_key>/', views.CaseDocumentDetail.as_view(), name='document'),
    # ex: /cases/<uuid:pk>/advice/
    path('<uuid:pk>/advice/', views.CaseAdvice.as_view(), name='case_advice'),
    # ex: /cases/<uuid:pk>/ecju-queries/
    path('<uuid:pk>/ecju-queries/', views.CaseEcjuQueries.as_view(), name='case_ecju_queries'),
    # ex: /cases/<uuid:pk>/ecju-queries/<uuid:ecju_pk>/
    path('<uuid:pk>/ecju-queries/<uuid:ecju_pk>/', views.EcjuQueryDetail.as_view(), name='case_ecju_query'),
]
