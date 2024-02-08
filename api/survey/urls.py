from django.urls import path
from api.survey.views import SurveyListCreateAPIView, SurveyDetailUpdateDeleteView

app_name = "survey"


urlpatterns = [
    path("", SurveyListCreateAPIView.as_view(), name="surveys"),
    path(
        "<uuid:pk>/",
        SurveyDetailUpdateDeleteView.as_view(),
        name="surveys_update",
    ),
]
