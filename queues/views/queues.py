from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from cases.views.search.queue import SearchQueue
from conf.authentication import GovAuthentication
from queues.helpers import get_queue
from queues.models import Queue
from queues.serializers import QueueCreateSerializer, QueueViewSerializer, QueueListSerializer


@permission_classes((permissions.AllowAny,))
class QueuesList(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Returns all queues
        """
        queues = Queue.objects.all()
        serializer = QueueListSerializer(queues, many=True)
        return JsonResponse(data={"queues": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data.copy()
        data["team"] = request.user.team.id
        serializer = QueueCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"queue": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes((permissions.AllowAny,))
class QueueDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Retrieve a queue instance (be that a system queue or a team queue)
        """
        queue = next(
            (queue for queue in SearchQueue.system(user=request.user) if queue.id == str(pk)), None
        ) or get_queue(pk=pk)

        serializer = QueueViewSerializer(queue)
        return JsonResponse(data=serializer.data)

    @swagger_auto_schema(request_body=QueueCreateSerializer)
    def put(self, request, pk):
        queue = get_queue(pk)
        data = request.data

        serializer = QueueCreateSerializer(instance=queue, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"queue": serializer.data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
