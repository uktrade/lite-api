from django.http import JsonResponse, Http404
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from queues.models import Queue
from queues.serializers import QueueSerializer


@permission_classes((permissions.AllowAny,))
class QueuesList(APIView):
    """
    List all queues
    """
    def get(self, request):
        queues = Queue.objects.filter().order_by('name')
        serializer = QueueSerializer(queues, many=True)
        return JsonResponse(data={'status': 'success', 'queues': serializer.data},
                            safe=False)

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = QueueSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'queue': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((permissions.AllowAny,))
class QueueDetail(APIView):
    """
    Retrieve a queue instance
    """
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
