import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import SharedAuthentication
from organisations.models import Organisation, Site
from organisations.serializers import SiteViewSerializer, SiteSerializer


class SitesList(APIView):
    """
    List all sites for an organisation/create site
    """

    authentication_classes = (SharedAuthentication,)

    def get(self, request, org_pk):
        """
        Endpoint for listing the Sites of an organisation
        An organisation must have at least one site
        """
        sites = list(Site.objects.filter(organisation=org_pk).order_by("name"))
        sites.sort(key=lambda x: x.id == x.organisation.primary_site.id, reverse=True)
        serializer = SiteViewSerializer(sites, many=True)
        return JsonResponse(data={"sites": serializer.data})

    @transaction.atomic
    def post(self, request, org_pk):
        with reversion.create_revision():
            organisation = Organisation.objects.get(pk=org_pk)
            data = JSONParser().parse(request)
            data["organisation"] = organisation.id
            serializer = SiteSerializer(data=data)

            if serializer.is_valid():
                # user information for gov users does not exist yet
                # reversion.set_user(request.user)
                # reversion.set_comment("Created Site")
                serializer.save()
                return JsonResponse(data={"site": serializer.data}, status=status.HTTP_201_CREATED)

            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR,)


class SiteDetail(APIView):
    """
    Show details for for a specific site/edit site
    """

    authentication_classes = (SharedAuthentication,)

    def get(self, request, org_pk, site_pk):
        Organisation.objects.get(pk=org_pk)
        site = Site.objects.get(pk=site_pk)

        serializer = SiteViewSerializer(site)
        return JsonResponse(data={"site": serializer.data})

    @transaction.atomic
    def put(self, request, org_pk, site_pk):
        Organisation.objects.get(pk=org_pk)
        site = Site.objects.get(pk=site_pk)

        with reversion.create_revision():
            serializer = SiteSerializer(instance=site, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()

                return JsonResponse(data={"site": serializer.data}, status=status.HTTP_200_OK)

            return JsonResponse(data={"errors": serializer.errors}, status=400)
