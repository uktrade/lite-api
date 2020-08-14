from django.urls import path

from api.letter_templates import views

app_name = "letter_templates"

urlpatterns = [
    path("", views.LetterTemplatesList.as_view(), name="letter_templates"),
    path("<uuid:pk>/", views.LetterTemplateDetail.as_view(), name="letter_template"),
    path("generate-preview/", views.TemplatePreview.as_view(), name="preview"),
]
