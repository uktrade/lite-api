from django.db import transaction
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import views

from cases.libraries.get_case import get_case
from cases.models import CaseAssignment
from cases.serializers import CaseAssignmentSerializer
from conf.authentication import GovAuthentication
from queues.constants import ALL_CASES_SYSTEM_QUEUE_ID, OPEN_CASES_SYSTEM_QUEUE_ID
from queues.helpers import get_queue
from users.libraries.get_user import get_user_by_pk


class CaseAssignments(views.APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        if ALL_CASES_SYSTEM_QUEUE_ID == str(pk) or OPEN_CASES_SYSTEM_QUEUE_ID == str(pk):
            return self._get_all_case_assignments()
        else:
            return self._get_case_assignments_for_specific_queue(pk)

    # noinspection PyMethodMayBeStatic
    def _get_all_case_assignments(self):
        case_assignments = CaseAssignment.objects.all()
        serializer = CaseAssignmentSerializer(case_assignments, many=True)
        return JsonResponse(data={"case_assignments": serializer.data})

    # noinspection PyMethodMayBeStatic
    def _get_case_assignments_for_specific_queue(self, pk):
        queue = get_queue(pk)
        case_assignments = CaseAssignment.objects.filter(queue=queue)
        serializer = CaseAssignmentSerializer(case_assignments, many=True)
        return JsonResponse(data={"case_assignments": serializer.data})

    @swagger_auto_schema(request_body=CaseAssignmentSerializer)
    @transaction.atomic
    def put(self, request, pk):
        """
        Assign users to cases on that queue
        """
        queue = get_queue(pk)
        data = request.data

        for assignment in data.get("case_assignments"):
            case = get_case(assignment["case_id"])
            users = [get_user_by_pk(i) for i in assignment["users"]]

            # Delete existing case assignments
            CaseAssignment.objects.filter(case=case, queue=queue).delete()

            # Create a new case assignment object between that case and those users
            case_assignment = CaseAssignment(case=case, queue=queue)
            case_assignment.users.set(users)
            case_assignment.save()

        # Return the newly set case assignments
        return self.get(request, pk)
