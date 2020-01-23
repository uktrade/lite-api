from django.urls import path

from documents import views

app_name = "documents"

urlpatterns = [
    path("<uuid:pk>/", views.DocumentDetail.as_view(), name="document"),
    path("test/", views.UploadTest.as_view(), name="upload",),
    path("case/<uuid:case_pk>/<uuid:file_pk>/", views.ExporterCaseDocumentDownload.as_view(), name="case_document",),
]
