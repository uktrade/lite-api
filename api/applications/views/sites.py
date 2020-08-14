from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from api.applications.libraries.sites_helpers import add_sites_to_application
from api.applications.libraries.get_applications import get_application
from api.conf.authentication import ExporterAuthentication
from api.conf.decorators import authorised_to_view_application
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.organisations.models import Site
from api.organisations.serializers import SiteListSerializer
from users.models import ExporterUser


class ApplicationSites(APIView):
    """ View sites belonging to an application or add them. """

    authentication_classes = (ExporterAuthentication,)

    @authorised_to_view_application(ExporterUser)
    def get(self, request, pk):
        sites = Site.objects.filter(sites_on_application__application_id=pk)
        serializer = SiteListSerializer(sites, many=True)
        return JsonResponse(data={"sites": serializer.data})

    @transaction.atomic
    @authorised_to_view_application(ExporterUser)
    def post(self, request, pk):
        application = get_application(pk)
        sites = Site.objects.filter(
            organisation_id=get_request_user_organisation_id(request), id__in=request.data.get("sites", [])
        )
        add_sites_to_application(request.user, sites, application)

        return JsonResponse(data={"sites": {}}, status=status.HTTP_201_CREATED)
