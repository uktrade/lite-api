from django.urls import path

from api.cases.generated_documents import views

app_name = "generated_documents"

urlpatterns = [
    path("", views.GeneratedDocuments.as_view(), name="generated_documents"),
    path("<uuid:dpk>/", views.GeneratedDocument.as_view(), name="generated_document"),
    path("<uuid:document_pk>/send/", views.GeneratedDocumentSend.as_view(), name="send_generated_document"),
    path("preview/", views.GeneratedDocumentPreview.as_view(), name="preview"),
]
