import reversion

from django.http import JsonResponse, Http404
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from organisations.libraries.get_site import get_site_by_organisation
from organisations.models import Organisation, Site
from organisations.serializers import SiteSerializer, SiteUpdateSerializer, SiteViewSerializer


class SiteViews(APIView):
    authentication_classes = (PkAuthentication,)
    """
    View for listing all sites for an organisation,
    adding sites and editing sites
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

    # FIXME: Needs to be completed
    def post(self, request, org_pk):
        """
        Endpoint for adding a site
        """
        data = JSONParser().parse(request)
        serializer = SiteSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'site': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, org_pk, site_pk):
        """
               Endpoint for updating a site
        """
        with reversion.create_revision():
            serializer = SiteUpdateSerializer(get_site_by_organisation(site_pk, org_pk),
                                              data=request.data,
                                              partial=True)
            if serializer.is_valid():
                serializer.save()

                # Store version meta-information
                reversion.set_user(request.user)
                reversion.set_comment("Created Site Revision")

                return JsonResponse(data={'site': serializer.data},
                                    status=status.HTTP_200_OK)
            return JsonResponse(data={'errors': serializer.errors},
                                status=400)


