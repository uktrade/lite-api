from django.conf import settings
from django.db import transaction
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
from conf.helpers import str_to_bool
from gov_users.libraries.get_gov_user import get_gov_user_by_pk
from queues.helpers import get_queue, get_all_cases_queue, get_open_cases_queue, get_filtered_cases, get_sorted_cases
from queues.models import Queue
from queues.serializers import QueueSerializer, QueueViewSerializer, QueueViewCaseDetailSerializer


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
        queue, cases = get_queue(pk, return_cases=True)
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


class CaseAssignments(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        if settings.ALL_CASES_SYSTEM_QUEUE_ID == str(pk) or settings.OPEN_CASES_SYSTEM_QUEUE_ID == str(pk):
            return self._get_all_case_assignments()
        else:
            return self._get_case_assignments_for_specific_queue(pk)

    # noinspection PyMethodMayBeStatic
    def _get_all_case_assignments(self):
        case_assignments = CaseAssignment.objects.all()
        serializer = CaseAssignmentSerializer(case_assignments, many=True)
        return JsonResponse(data={'case_assignments': serializer.data})

    # noinspection PyMethodMayBeStatic
    def _get_case_assignments_for_specific_queue(self, pk):
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
