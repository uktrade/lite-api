from rest_framework.views import APIView

from conf.serializers import response_serializer
from static.denial_reasons.models import DenialReason
from static.denial_reasons.serializers import DenialReasonSerializer


class DenialReasonsList(APIView):
    def get(self, request):
        denial_reasons = DenialReason.objects.all()
        return response_serializer(DenialReasonSerializer, obj=denial_reasons, many=True)
