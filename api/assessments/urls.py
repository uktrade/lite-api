from django.urls import path

from api.assessments import views

app_name = "assessments"

urlpatterns = [
    path(
        "make-assessments/<uuid:case_pk>/",
        views.MakeAssessmentsView.as_view(),
        name="make_assessments",
    ),
]
