from django.urls import path

from api.reports.views import EmailReportView

app_name = "mail"

urlpatterns = [
    path("email-report/", EmailReportView.as_view(), name="email-report"),
]
