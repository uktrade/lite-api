from django.http import JsonResponse, Http404

from rest_framework.views import APIView
from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.models import Organisation, Site
from organisations.serializers import SiteViewSerializer


class SiteList(APIView):

    """
    View for listing all sites for an organisation,
    adding sites and editing sites
    """

    def get(self, request, pk):
        # the organisation should not be obtained from the user account
        # organisation = get_organisation_by_user(request.user)

        sites = Site.objects.filter(organisation=pk)
        serializer = SiteViewSerializer(sites, many=True)
        return JsonResponse(data={'sites': serializer.data},
                            safe=False)


