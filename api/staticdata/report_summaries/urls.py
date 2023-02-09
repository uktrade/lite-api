from django.urls import path

from . import views


app_name = "report_summaries"

urlpatterns = [
    path("prefixes/", views.ReportSummaryPrefixView.as_view(), name="prefix"),
    path("subjects/", views.ReportSummarySubjectView.as_view(), name="subject"),
]
