from django.db.models import When, Case, IntegerField
from django.http import JsonResponse
from rest_framework import status, generics
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.helpers import str_to_bool
from queues.models import Queue
from queues.serializers import QueueCreateSerializer, QueueViewSerializer, QueueListSerializer
from queues.service import get_queue


class QueuesList(generics.ListAPIView):
    authentication_classes = (GovAuthentication,)
    queryset = Queue.objects.all()
    serializer_class = QueueListSerializer

    def filter_queryset(self, queryset):

        if str_to_bool(self.request.GET.get("users_team_first", "False")):
            return queryset.annotate(
                users_team=(Case(When(team=self.request.user.team, then=1), default=0, output_field=IntegerField()))
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
        queue = get_queue(request.user, pk)

        serializer = QueueViewSerializer(queue)
        return JsonResponse(data=serializer.data)

    def put(self, request, pk):
        queue = get_queue(request.user, pk)
        data = request.data

        serializer = QueueCreateSerializer(instance=queue, data=data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse(data={"queue": serializer.data})
