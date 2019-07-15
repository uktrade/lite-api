from django.urls import path

from cases import views

app_name = 'cases'

urlpatterns = [
    path('<uuid:pk>/', views.CaseDetail.as_view(), name='case'),
    path('<uuid:pk>/case_notes/', views.CaseNoteList.as_view(), name='case_notes'),
    # ex: /cases/<uuid:pk>/activity/
    # ex: /cases/<uuid:pk>/activity/?fields=activity,status
    path('<uuid:pk>/activity/', views.ActivityList.as_view(), name='activity'),
    # ex: /cases/<uuid:pk>/case-flags/
    path('<uuid:pk>/case-flags/', views.CaseFlagsList.as_view(), name='case_flags'),
]
