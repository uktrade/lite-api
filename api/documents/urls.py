from django.urls import path

from api.documents import views

app_name = "documents"

urlpatterns = [
    path("<uuid:pk>/", views.DocumentDetail.as_view(), name="document"),
    path("certificate/", views.DownloadSigningCertificate.as_view(), name="certificate"),
    path("stream/<uuid:pk>/", views.DocumentStream.as_view(), name="document_stream"),
]
