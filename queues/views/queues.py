from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, generics
from rest_framework.decorators import permission_classes
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from cases.libraries.get_case import get_case
from cases.models import CaseAssignment, Case
from cases.serializers import CaseAssignmentSerializer, CaseDetailSerializer, CaseSerializer
from conf.authentication import GovAuthentication
from conf.helpers import str_to_bool
from queues.helpers import get_queue, get_all_cases_queue, get_open_cases_queue, get_filtered_cases, get_sorted_cases, \
    get_all_my_team_cases_queue
from queues.models import Queue
from queues.serializers import QueueSerializer, QueueViewSerializer, QueueViewCaseDetailSerializer
from users.libraries.get_user import get_user_by_pk


@permission_classes((permissions.AllowAny,))
class QueuesList(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Gets all queues.
        Optionally includes the system defined, pseudo queues "All cases" and "Open cases"
        """
        include_system_queues = str_to_bool(request.GET.get('include_system_queues', False))

        queues = Queue.objects.all().order_by('name')

        if include_system_queues:
            queues = list(queues)
            queues.insert(0, get_open_cases_queue())
            queues.insert(0, get_all_cases_queue())
            queues.insert(0, get_all_my_team_cases_queue(request.user.team))

        serializer = QueueViewSerializer(queues, many=True)

        return JsonResponse(data={'queues': serializer.data})

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
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Retrieve a queue instance
        """
        team = request.user.team
        queue, cases = get_queue(pk=pk, return_cases=True, team=team)
        cases = get_filtered_cases(request, queue.id, cases)
        cases = get_sorted_cases(request, queue.id, cases)

        queue = queue.__dict__
        queue['cases'] = cases
        serializer = QueueViewCaseDetailSerializer(queue)
        return JsonResponse(data={'queue': serializer.data})

    @swagger_auto_schema(request_body=QueueSerializer)
    def put(self, request, pk):
        queue = get_queue(pk)
        data = request.data.copy()
        serializer = QueueSerializer(instance=queue, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'queue': serializer.data})
        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
