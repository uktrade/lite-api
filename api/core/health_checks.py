from health_check.backends import BaseHealthCheckBackend
from django.http import HttpResponse

from rest_framework import status


class ServiceAvailableHealthCheck(BaseHealthCheckBackend):
    #: The status endpoints will respond with a 200 status code
    #: even if the check errors.
    critical_service = False

    def check_status(self):
        return HttpResponse(status=status.HTTP_200_OK)
