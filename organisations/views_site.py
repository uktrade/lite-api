from django.http import JsonResponse, Http404

from rest_framework.views import APIView
from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.models import Organisation, Site
from organisations.serializers import SiteSerializer


class ApplicationList(APIView):

    """
    View for listing all sites for an organisation,
    adding sites and editing sites
    """

    def get(self, request):
        organisation = get_organisation_by_user(request.user)
        sites = Site.Application.objects.filter(organisation=organisation)

        serializer = SiteSerializer(sites, many=True)
        return JsonResponse(data={'sites': serializer.data},
                            safe=False)


