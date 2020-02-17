from django.urls import path

from cases.generated_documents import views

app_name = "generated_documents"

urlpatterns = [
    path("", views.InternalViewGeneratedDocuments.as_view(), name="generated_documents"),
    path("<uuid:pk>/", views.GeneratedDocument.as_view(), name="generated_document"),
    path("exporter/", views.ExporterViewGeneratedDocuments.as_view(), name="exporter_generated_documents"),
    path("preview/", views.GeneratedDocumentPreview.as_view(), name="preview"),
]
