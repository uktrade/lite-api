from django.urls import path

from . import views


app_name = "report_summaries"

urlpatterns = [
    path("prefixes/", views.ReportSummaryPrefixesListView.as_view(), name="prefixes"),
    path("prefixes/<uuid:pk>/", views.ReportSummaryPrefixDetailView.as_view(), name="prefix"),
    path("subjects/", views.ReportSummarySubjectsListView.as_view(), name="subjects"),
    path("subjects/<uuid:pk>/", views.ReportSummarySubjectDetailView.as_view(), name="subject"),
]
