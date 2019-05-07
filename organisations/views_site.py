import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.libraries.get_site import get_site_with_organisation
from organisations.models import Site
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
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        data['organisation'] = organisation.id
        serializer = SiteCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'site': serializer.data},
                                status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

            print(serializer.errors)
            return JsonResponse(data={'errors': serializer.errors},
                                status=400)
