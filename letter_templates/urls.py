from django.urls import path

from letter_templates import views

app_name = "letter_templates"

urlpatterns = [
    # ex: /letter-templates/ - List all letter templates
    path("", views.LetterTemplatesList.as_view(), name="letter_templates"),
    # ex: /letter-templates/<uuid:pk>/ - Details of a particular letter template
    path("<uuid:pk>/", views.LetterTemplateDetail.as_view(), name="letter_template"),
]
