from django.http import JsonResponse, Http404
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from queues.libraries.get_queue import get_queue
from queues.models import Queue
from queues.serializers import QueueSerializer, QueueViewSerializer, CaseAssignmentSerializer


@permission_classes((permissions.AllowAny,))
class QueuesList(APIView):
    """
    List all queues
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        queues = Queue.objects.filter().order_by('name')
        serializer = QueueViewSerializer(queues, many=True)
        return JsonResponse(data={'queues': serializer.data})

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = QueueSerializer(data=data, partial=True)

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
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        queue = get_queue(pk)
        serializer = QueueViewSerializer(queue)
        return JsonResponse(data={'queue': serializer.data})

    def put(self, request, pk):
        queue = get_queue(pk)
        data = request.data.copy()
        serializer = QueueSerializer(instance=queue, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'queue': serializer.data})
        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class CaseAssignment(APIView):
    """
    Update user to case assignments on a queue
    """
    def put(self, request, pk):
        queue = get_queue(pk)
        data = request.data
        data['queue'] = queue.id
        print('data', data)

        serializer = CaseAssignmentSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            return JsonResponse(data={'case': serializer.data},
                                status=status.HTTP_200_OK)

        print('serializer errors', serializer.errors)
        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
