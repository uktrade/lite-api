from django.urls import path

from . import views


app_name = "report_summaries"

urlpatterns = [
    path("prefixes/", views.ReportSummaryPrefixesListView.as_view(), name="prefixes"),
    path("subjects/", views.ReportSummarySubjectsListView.as_view(), name="subjects"),
]
