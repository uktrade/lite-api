from django.http import JsonResponse
from rest_framework.views import APIView
from api.core.authentication import HawkOnlyAuthentication

from api.staticdata.flag_aliases.serializers import FlagAliasesSerializers
from api.queues.models import Queue


class FlagAliases(APIView):
    authentication_classes = (HawkOnlyAuthentication,)

    def get(self, request):
        queues = Queue.objects.filter(alias__isnull=False)
        serializer = FlagAliasesSerializers(queues, many=True)
        return JsonResponse(data={"queue_aliases": serializer.data})
