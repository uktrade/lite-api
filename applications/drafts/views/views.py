from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.libraries.get_applications import get_application
from conf.authentication import ExporterAuthentication
from organisations.libraries.get_organisation import get_organisation_by_user


class DraftDetail(APIView):
    """
    Retrieve or delete a draft instance
    """
    authentication_classes = (ExporterAuthentication,)
