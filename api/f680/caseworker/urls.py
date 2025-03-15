from django.urls import path

from api.f680.caseworker.views import F680RecommendationViewSet

app_name = "caseworker_f680"

urlpatterns = [
    path(
        "<uuid:pk>/recommendation/",
        F680RecommendationViewSet.as_view({"get": "list", "post": "create"}),
        name="recommendation",
    ),
]
