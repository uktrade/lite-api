import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.libraries.get_site import get_site_with_organisation
from organisations.models import Organisation, Site
from organisations.serializers import SiteViewSerializer, SiteCreateSerializer, SiteUpdateSerializer


class SiteList(APIView):
    authentication_classes = (PkAuthentication,)
    """
    List all sites for an organisation/create site
    """

    def get(self, request):
        organisation = get_organisation_by_user(request.user)
        sites = Site.objects.filter(organisation=organisation)

        serializer = SiteViewSerializer(sites, many=True)
        return JsonResponse(data={'sites': serializer.data},
                            safe=False)

    @transaction.atomic
    def post(self, request):
        with reversion.create_revision():
            organisation = get_organisation_by_user(request.user)
            data = JSONParser().parse(request)
            data['organisation'] = organisation.id
            serializer = SiteCreateSerializer(data=data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse(data={'site': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrgSiteList(APIView):
    authentication_classes = (PkAuthentication,)
    """
    List all sites for an organisation/create site
    """

    def get(self, request, org_pk, site_pk=''):
        """
        Endpoint for listing the Sites of an organisation
        An organisation must have at least one site
        """

        sites = Site.objects.filter(organisation=org_pk)
        serializer = SiteViewSerializer(sites, many=True)
        return JsonResponse(data={'sites': serializer.data},
                            safe=False)

    @transaction.atomic
    def post(self, request, org_pk):
        with reversion.create_revision():
            # organisation = get_organisation_by_user(request.user)
            organisation = Organisation.objects.get(pk=org_pk)
            data = JSONParser().parse(request)
            data['organisation'] = organisation.id
            serializer = SiteCreateSerializer(data=data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse(data={'site': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # def post(self, request, org_pk):
    #     """
    #     Endpoint for adding a site
    #     """
    #     data = JSONParser().parse(request)
    #     serializer = SiteSerializer(data=data)
    #
    #     if serializer.is_valid():
    #         serializer.save()
    #         return JsonResponse(data={'site': serializer.data},
    #                             status=status.HTTP_201_CREATED)
    #
    #     return JsonResponse(data={'errors': serializer.errors},
    #                         status=status.HTTP_400_BAD_REQUEST)




class SiteDetail(APIView):
    authentication_classes = (PkAuthentication,)
    """
    Show details for for a specific site/edit site
    """

    def get(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        site = get_site_with_organisation(pk, organisation)

        serializer = SiteViewSerializer(site)
        return JsonResponse(data={'site': serializer.data},
                            safe=False)

    @transaction.atomic
    def put(self, request, pk):
        organisation = get_organisation_by_user(request.user)

        with reversion.create_revision():
            serializer = SiteUpdateSerializer(get_site_with_organisation(pk, organisation),
                                              data=request.data,
                                              partial=True)
            if serializer.is_valid():
                serializer.save()
                reversion.set_user(request.user)
                reversion.set_comment("Created Site Revision")

                return JsonResponse(data={'site': serializer.data},
                                    status=status.HTTP_200_OK)

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)
