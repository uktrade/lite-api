from django.urls import path

from .views import LetterTemplatesList

app_name = "caseworker_letter_templates"

urlpatterns = [
    path("", LetterTemplatesList.as_view(), name="list"),
]
