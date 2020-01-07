from django.http import JsonResponse
from rest_framework.views import APIView

from applications.libraries.get_applications import get_case_payload
from cases.enums import CaseTypeEnum
from cases.models import Case
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users
from parties.serializers import PartySerializer
from users.models import ExporterUser


class ExistingParties(APIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application):
        parties = []
        cases = Case.objects.filter(
            organisation=application.organisation, type=CaseTypeEnum.APPLICATION, submitted_at__isnull=False
        )

        for case in cases:
            payload = get_case_payload(case)
            parties.append(payload.end_user)
            parties.append(payload.consignee)

        parties = PartySerializer(parties, many=True).data
        return JsonResponse(data={"parties": parties})
