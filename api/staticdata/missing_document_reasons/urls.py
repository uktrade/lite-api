from django.urls import path

from api.staticdata.missing_document_reasons import views

app_name = "missing_document_reasons"

urlpatterns = [
    path("", views.MissingDocumentReasons.as_view(), name="missing_document_reasons"),
]
