from django.urls import path

from . import views

app_name = "appeals"

urlpatterns = [
    path(
        "<uuid:pk>/documents/",
        views.AppealCreateDocumentAPIView.as_view(),
        name="documents",
    ),
    path(
        "<uuid:pk>/documents/<uuid:document_pk>/",
        views.AppealDocumentAPIView.as_view(),
        name="document",
    ),
]
