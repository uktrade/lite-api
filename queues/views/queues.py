from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.helpers import str_to_bool
from queues.helpers import get_queue, get_all_cases_queue, get_open_cases_queue, get_all_my_team_cases_queue
from queues.models import Queue
from queues.serializers import QueueCreateSerializer, QueueViewSerializer


@permission_classes((permissions.AllowAny,))
class QueuesList(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Lists all queues
        Optionally includes system queues
        """
        queues = Queue.objects.all()
        include_system_queues = str_to_bool(request.GET.get('include_system_queues', False))

        if include_system_queues:
            queues = list(queues)
            queues.insert(0, get_all_my_team_cases_queue(request.user.team))
            queues.insert(0, get_open_cases_queue())
            queues.insert(0, get_all_cases_queue())

        serializer = QueueViewSerializer(queues, many=True)

        return JsonResponse(data={'queues': serializer.data})

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = QueueCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'queue': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((permissions.AllowAny,))
class QueueDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Retrieve a queue instance
        """
        team = request.user.team
        queue = get_queue(pk=pk, team=team)
        serializer = QueueViewSerializer(queue)
        return JsonResponse(data={'queue': serializer.data})

    @swagger_auto_schema(request_body=QueueCreateSerializer)
    def put(self, request, pk):
        queue = get_queue(pk)
        data = request.data

        serializer = QueueCreateSerializer(instance=queue, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'queue': serializer.data})

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
