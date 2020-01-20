from django.urls import path

from documents import views

app_name = "documents"

urlpatterns = [
    path("<uuid:pk>/", views.DocumentDetail.as_view(), name="document"),
    path("<uuid:good_pk>/<uuid:file_pk>/download/", views.ExporterGoodDocumentDownload.as_view(), name="download"),
]
