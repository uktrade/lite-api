from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView


from api.reports.tasks import email_reports_task


class EmailReportView(APIView):
    def get(self, request):
        email_reports_task.now()

        return HttpResponse(status=status.HTTP_200_OK)
