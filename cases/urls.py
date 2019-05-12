from django.urls import path

from cases import views

app_name = 'cases'

urlpatterns = [
    path('<uuid:pk>/', views.CaseDetail.as_view(), name='case'),
    path('<uuid:pk>/case_notes/', views.CaseNoteList.as_view(), name='case_notes'),
]
