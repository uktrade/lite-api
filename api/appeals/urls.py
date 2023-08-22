from django.urls import path

from . import views

app_name = "appeals"

urlpatterns = [
    path(
        "<uuid:pk>/documents/",
        views.AppealDocuments.as_view(),
        name="documents",
    ),
]
