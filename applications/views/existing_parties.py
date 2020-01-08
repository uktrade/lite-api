from django.http import JsonResponse
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users
from parties.serializers import PartySerializer
from parties.models import Party
from users.models import ExporterUser


class ExistingParties(APIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application):
        parties = Party.objects.filter(organisation=application.organisation)
        parties = PartySerializer(parties, many=True).data
        return JsonResponse(data={"parties": parties})
