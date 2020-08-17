from django.db.models import When, Case, BinaryField
from django.http import JsonResponse
from rest_framework import status, generics
from rest_framework.views import APIView

from api.core.authentication import GovAuthentication
from api.core.helpers import str_to_bool
from api.queues.models import Queue
from api.queues.serializers import QueueCreateSerializer, QueueViewSerializer, QueueListSerializer
from api.queues.service import get_queue, get_queues_qs, get_system_queues


class QueuesList(generics.ListAPIView):
    authentication_classes = (GovAuthentication,)
    queryset = Queue.objects.select_related("team", "countersigning_queue").all()
    serializer_class = QueueListSerializer

    def get(self, request, *args, **kwargs):
        include_system = request.GET.get("include_system", False)
        disable_pagination = request.GET.get("disable_pagination", False)

        if str_to_bool(include_system) and str(disable_pagination):
            system_queue_data = get_system_queues()
            work_queue_data = self.get_serializer(get_queues_qs(), many=True).data
            return JsonResponse(data=system_queue_data + work_queue_data, safe=False, status=status.HTTP_200_OK)

        return super().get(request, *args, **kwargs)

    def filter_queryset(self, queryset):
        users_team_first = self.request.GET.get("users_team_first", False)
        name = self.request.GET.get("name")

        if name:
            queryset = queryset.filter(name__icontains=name)
        if str_to_bool(users_team_first):
            queryset = queryset.annotate(
                users_team=(Case(When(team=self.request.user.team, then=1), default=0, output_field=BinaryField()))
            ).order_by("-users_team")

        return queryset

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
        queue = get_queue(pk)

        serializer = QueueViewSerializer(queue)
        return JsonResponse(data=serializer.data)

    def put(self, request, pk):
        queue = get_queue(pk)
        data = request.data

        serializer = QueueCreateSerializer(instance=queue, data=data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse(data={"queue": serializer.data}, status=status.HTTP_200_OK)
