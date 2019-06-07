from django.http import JsonResponse
from rest_framework.views import APIView

from static.denial_reasons.models import DenialReason
from static.denial_reasons.serializers import DenialReasonSerializer


class DenialReasonsList(APIView):
    def get(self, request):
        denial_reasons = DenialReason.objects.all()
        serializer = DenialReasonSerializer(denial_reasons, many=True)
        return JsonResponse(data={'denial_reasons': serializer.data})
