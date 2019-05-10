from django.urls import path

from cases import views

app_name = 'cases'

urlpatterns = [
    path('<uuid:pk>/', views.CaseDetail.as_view()),
    path('<uuid:pk>/case_notes/', views.CaseNoteList.as_view()),
]
