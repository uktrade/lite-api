from django.urls import path

from documents import views

app_name = "documents"

urlpatterns = [
    path("<uuid:pk>/", views.DocumentDetail.as_view(), name="document"),
    path("case/<uuid:case_pk>/<uuid:file_pk>/download/", views.ExporterCaseDocumentDownload.as_view(), name="download"),
]
