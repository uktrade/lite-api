from django.http import JsonResponse, Http404
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
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
        return JsonResponse(data={'status': 'success', 'queues': serializer.data},
                            safe=False)


@permission_classes((permissions.AllowAny,))
class QueueDetail(APIView):
    """
    Retrieve a queue instance
    """
    authentication_classes = (GovAuthentication,)

    def get_object(self, pk):
        try:
            queue = Queue.objects.get(pk=pk)
            return queue
        except Queue.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        queue = self.get_object(pk)
        serializer = QueueSerializer(queue)
        return JsonResponse(data={'status': 'success', 'queue': serializer.data})
