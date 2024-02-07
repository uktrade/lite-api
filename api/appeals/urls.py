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
    path(
        "<uuid:pk>/documents/<uuid:document_pk>/stream/",
        views.AppealDocumentStreamAPIView.as_view(),
        name="document_stream",
    ),
]
