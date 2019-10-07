from django.urls import path

from letter_templates import views

app_name = 'letter_templates'

urlpatterns = [
    path('', views.LetterTemplatesList.as_view(), name='letter_templates'),
    path('<str:pk>/', views.LetterTemplatesDetail.as_view(), name='letter_template')
]
