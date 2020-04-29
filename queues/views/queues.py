from collections import OrderedDict

from django.http import JsonResponse
from rest_framework import status, generics
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.custom_views import OptionalPaginationView
from conf.helpers import str_to_bool
from queues.constants import SYSTEM_QUEUE_NAME_MAP
from queues.models import Queue
from queues.serializers import QueueCreateSerializer, QueueViewSerializer, QueueListSerializer
from queues.service import get_queue


class QueuesList(OptionalPaginationView):
    authentication_classes = (GovAuthentication,)
    queryset = Queue.objects.all()
    serializer_class = QueueListSerializer

    def get(self, request, *args, **kwargs):
        include_system = request.GET.get("include_system", False)

        if str_to_bool(include_system):
            system_queues = [
                {"id": id, "name": name}
                for id, name in sorted(SYSTEM_QUEUE_NAME_MAP.items(), key=lambda queue_name_map: queue_name_map[1])
            ]
            work_queues = list(self.get_queryset())

            data = self.get_serializer(system_queues + work_queues, many=True).data
            return JsonResponse(data={"results": data}, status=status.HTTP_200_OK)
        else:
            return super().get(request, *args, **kwargs)

    def post(self, request):
        data = request.data.copy()
        data["team"] = request.user.team.id
        serializer = QueueCreateSerializer(data=data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse(data={"queue": serializer.data}, status=status.HTTP_201_CREATED)


class QueueDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Retrieve a queue instance (be that a system queue or a team queue)
        """
        queue = get_queue(request.user, pk)

        serializer = QueueViewSerializer(queue)
        return JsonResponse(data=serializer.data)

    def put(self, request, pk):
        queue = get_queue(request.user, pk)
        data = request.data

        serializer = QueueCreateSerializer(instance=queue, data=data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse(data={"queue": serializer.data}, status=status.HTTP_200_OK)
