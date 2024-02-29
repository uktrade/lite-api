from django.urls import path
from api.survey.views import SurveyCreateAPIView, SurveyDetailUpdateAPIView

app_name = "survey"


urlpatterns = [
    path("", SurveyCreateAPIView.as_view(), name="surveys"),
    path(
        "<uuid:pk>/",
        SurveyDetailUpdateAPIView.as_view(),
        name="surveys_update",
    ),
]
