from django.urls import path

from letter_templates import views

app_name = 'letter_templates'

urlpatterns = [
    # ex: /letter-templates/ - List all letter templates
    path('', views.LetterTemplatesList.as_view(), name='letter_templates'),
    # ex: /letter-templates/<uuid:pk>/ - Details of a particular letter template
    path('<uuid:pk>/', views.LetterTemplateDetail.as_view(), name='letter_template'),
    # ex: /letter-templates/layouts/
    path('layouts/', views.LetterLayoutsList.as_view(), name='letter_layouts'),
    # ex: /letter-templates/layouts/<str:pk>/
    path('layouts/<str:pk>/', views.LetterLayoutDetail.as_view(), name='letter_layout'),
]
