from django.urls import path

from static.missing_document_reasons import views

app_name = "missing_document_reasons"

urlpatterns = [
    path("", views.MissingDocumentReasons.as_view(), name="missing_document_reasons"),
]
