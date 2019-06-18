from django.http import JsonResponse, Http404
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from queues.libraries.get_queue import get_queue
from queues.models import Queue
from queues.serializers import QueueSerializer


@permission_classes((permissions.AllowAny,))
class QueuesList(APIView):
    """
    List all queues
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        queues = Queue.objects.filter().order_by('name')
        serializer = QueueSerializer(queues, many=True)
        return JsonResponse(data={'queues': serializer.data})


@permission_classes((permissions.AllowAny,))
class QueueDetail(APIView):
    """
    Retrieve a queue instance
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        queue = get_queue(pk)
        serializer = QueueSerializer(queue)
        return JsonResponse(data={'queue': serializer.data})
