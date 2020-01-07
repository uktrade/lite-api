from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.helpers import str_to_bool
from queues.helpers import get_queue, get_queues
from queues.serializers import QueueCreateSerializer, QueueViewSerializer


@permission_classes((permissions.AllowAny,))
class QueuesList(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Gets all queues.
        Optionally includes the system defined, pseudo queues "All cases" and "Open cases"
        """
        queues = get_queues(
            include_system_queues=str_to_bool(request.GET.get("include_system_queues", False)), user=request.user
        )

        serializer = QueueViewSerializer(queues, many=True)
        return JsonResponse(data={"queues": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        data = JSONParser().parse(request)
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
        Retrieve a queue instance
        """
        queue = get_queue(pk=pk, user=request.user)
        serializer = QueueViewSerializer(queue)
        return JsonResponse(data={"queue": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=QueueCreateSerializer)
    def put(self, request, pk):
        queue = get_queue(pk)
        data = request.data

        serializer = QueueCreateSerializer(instance=queue, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"queue": serializer.data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
