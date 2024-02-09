from django.urls import path
from api.survey.views import SurveyListCreateAPIView, SurveyDetailUpdateAPIView

app_name = "survey"


urlpatterns = [
    path("", SurveyListCreateAPIView.as_view(), name="surveys"),
    path(
        "<uuid:pk>/",
        SurveyDetailUpdateAPIView.as_view(),
        name="surveys_update",
    ),
]
