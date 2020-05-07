from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.libraries.sites_helpers import add_sites_to_application
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users
from organisations.libraries.get_organisation import get_request_user_organisation_id
from organisations.models import Site
from organisations.serializers import SiteListSerializer
from users.models import ExporterUser


class ApplicationSites(APIView):
    """ View sites belonging to an application or add them. """

    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application):
        sites = Site.objects.filter(sites_on_application__application=application)
        serializer = SiteListSerializer(sites, many=True)
        return JsonResponse(data={"sites": serializer.data})

    @transaction.atomic
    @authorised_users(ExporterUser)
    def post(self, request, application):
        sites = Site.objects.filter(
            organisation_id=get_request_user_organisation_id(request), id__in=request.data.get("sites", [])
        )
        add_sites_to_application(request.user, sites, application)

        return JsonResponse(data={"sites": {}}, status=status.HTTP_201_CREATED)
