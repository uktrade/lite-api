from django.urls import path

from cases import views

app_name = 'cases'

urlpatterns = [
    path('<uuid:pk>/', views.CaseDetail.as_view(), name='case'),
    path('<uuid:pk>/case_notes/', views.CaseNoteList.as_view(), name='case_notes'),
    # ex: /cases/<uuid:pk>/activity/?fields=activity,status,flags
    path('<uuid:pk>/activity/', views.CaseActivity.as_view(), name='activity'),
    # ex: /cases/<uuid:pk>/documents/
    path('<uuid:pk>/documents/', views.CaseDocuments.as_view(), name='documents'),
    # ex: /cases/<uuid:pk>/documents/<uuid:file_pk>/
    path('<uuid:pk>/documents/<str:s3_key>/', views.CaseDocumentDetail.as_view(), name='document'),
    # ex: /cases/<uuid:pk>/flags/
    path('<uuid:pk>/flags/', views.CaseFlagsAssignment.as_view(), name='case_flags'),
    # ex: /cases/<uuid:pk>/advice/
    path('<uuid:pk>/advice/', views.CaseAdvice.as_view(), name='case_advice'),
]
