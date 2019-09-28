from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.helpers import str_to_bool
from conf.serializers import response_serializer
from queues.helpers import get_queue, get_queues
from queues.models import Queue
from queues.serializers import QueueCreateSerializer, QueueViewSerializer


@permission_classes((permissions.AllowAny,))
class QueuesList(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Gets all queues.
        Optionally includes the system defined, pseudo queues "All cases" and "Open cases"
        """
        queues = get_queues(request.user.team, str_to_bool(request.GET.get('include_system_queues', False)))

        return response_serializer(serializer=QueueViewSerializer, obj=queues, many=True, response_name='queues')

    def post(self, request):
        data = JSONParser().parse(request)
        return response_serializer(serializer=QueueCreateSerializer, data=data, object_class=Queue)


@permission_classes((permissions.AllowAny,))
class QueueDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Retrieve a queue instance
        """
        team = request.user.team
        queue = get_queue(pk=pk, team=team)
        return response_serializer(serializer=QueueViewSerializer, object_class=Queue, obj=queue)

    @swagger_auto_schema(request_body=QueueCreateSerializer)
    def put(self, request, pk):
        data = request.data
        return response_serializer(serializer=QueueCreateSerializer, object_class=Queue, data=data, pk=pk, partial=True)
