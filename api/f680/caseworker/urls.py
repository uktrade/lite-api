from django.urls import path

from api.f680.caseworker.views import F680RecommendationViewSet, F680OutcomeViewSet, F680OutcomeDocumenViewSet

app_name = "caseworker_f680"

urlpatterns = [
    path(
        "<uuid:pk>/recommendation/",
        F680RecommendationViewSet.as_view(
            {
                "get": "list",
                "post": "create",
                "delete": "destroy",
            }
        ),
        name="recommendation",
    ),
    path(
        "<uuid:pk>/outcome/",
        F680OutcomeViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="outcome",
    ),
    path(
        "<uuid:pk>/outcome/<uuid:outcome_id>/",
        F680OutcomeViewSet.as_view(
            {
                "delete": "destroy",
            }
        ),
        name="delete_outcome",
    ),
    path(
        "<uuid:pk>/outcome_document/",
        F680OutcomeDocumenViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="outcome_document",
    ),
]
