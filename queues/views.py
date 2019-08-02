from json import loads

from django.db import transaction
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from cases.libraries.get_case import get_case
from cases.models import CaseAssignment
from cases.serializers import CaseAssignmentSerializer
from conf.authentication import GovAuthentication
from gov_users.libraries.get_gov_user import get_gov_user_by_pk
from queues.helpers import get_queue
from queues.models import Queue
from queues.serializers import QueueSerializer, QueueViewSerializer
from static.statuses.models import CaseStatus


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
        cases = queue.cases.annotate(
            status__priority=Coalesce('application__status__priority', 'clc_query__status__priority')
        )

        kwargs = {}
        case_type = request.GET.get('case_type', None)
        if case_type:
            kwargs['case_type__name'] = case_type

        status = request.GET.get('status', None)
        if status:
            kwargs['status__priority'] = CaseStatus.objects.get(status=status).priority

        cases = cases.filter(**kwargs)

        sort = request.GET.get('sort', None)
        if sort:
            kwargs = []
            sort = loads(sort)
            if 'status' in sort:
                order = '-' if sort['status'] == 'desc' else ''
                kwargs.append(order + 'status__priority')

            # Add other `if` conditions before next line to sort by more fields
            cases = cases.order_by(*kwargs)

        queue = queue.__dict__
        queue['cases'] = list(cases.all())

        serializer = QueueViewSerializer(queue)
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


class CaseAssignments(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Get all case assignments for that queue
        """
        queue = get_queue(pk)
        case_assignments = CaseAssignment.objects.filter(queue=queue)
        serializer = CaseAssignmentSerializer(case_assignments, many=True)
        return JsonResponse(data={'case_assignments': serializer.data})

    @swagger_auto_schema(request_body=CaseAssignmentSerializer)
    @transaction.atomic
    def put(self, request, pk):
        """
        Assign users to cases on that queue
        """
        queue = get_queue(pk)
        data = request.data

        for assignment in data.get('case_assignments'):
            case = get_case(assignment['case_id'])
            users = [get_gov_user_by_pk(i) for i in assignment['users']]

            # Delete existing case assignments
            CaseAssignment.objects.filter(case=case, queue=queue).delete()

            # Create a new case assignment object between that case and those users
            case_assignment = CaseAssignment(case=case, queue=queue)
            case_assignment.users.set(users)
            case_assignment.save()

        # Return the newly set case assignments
        return self.get(request, pk)
