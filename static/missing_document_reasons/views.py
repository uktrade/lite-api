from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK

from api.conf.authentication import SharedAuthentication
from static.missing_document_reasons.enums import GoodMissingDocumentReasons


class MissingDocumentReasons(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        reasons = [{"key": choice[0], "value": choice[1]} for choice in GoodMissingDocumentReasons.choices]
        return JsonResponse(data={"reasons": reasons}, status=HTTP_200_OK)
