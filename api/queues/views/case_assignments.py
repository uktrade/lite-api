from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework import views

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.libraries.get_case import get_case
from api.cases.models import CaseAssignment
from api.cases.serializers import CaseAssignmentSerializer
from api.core.authentication import GovAuthentication
from api.core.helpers import str_to_bool
from api.queues.constants import ALL_CASES_QUEUE_ID, OPEN_CASES_QUEUE_ID
from api.queues.helpers import get_queue
from api.users.libraries.get_user import get_user_by_pk


class CaseAssignments(views.APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        if ALL_CASES_QUEUE_ID == str(pk) or OPEN_CASES_QUEUE_ID == str(pk):
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

            if str_to_bool(data.get("remove_existing_assignments")):
                CaseAssignment.objects.filter(case=case, queue=queue).delete()

            # Create a new case assignment object between that case and those users
            for user in users:
                try:
                    CaseAssignment.objects.get(case=case, queue=queue, user=user)
                except CaseAssignment.DoesNotExist:
                    case_assignment = CaseAssignment(case=case, queue=queue, user=user)
                    case_assignment.save(audit_user=request.user, user=user, audit_note=data.get("note"))

            # Add to queue
            case.queues.add(queue)

        # Return the newly set case assignments
        return self.get(request, pk)


class CaseAssignmentDetail(views.APIView):
    authentication_classes = (GovAuthentication,)

    def _create_assignment_removal_audit_entry(self, assignment, actor):
        if assignment.user.first_name and assignment.user.last_name:
            removed_user_name = f"{assignment.user.first_name} {assignment.user.last_name}"
        else:
            removed_user_name = assignment.user.email
        audit_trail_service.create(
            actor=actor,
            verb=AuditType.REMOVE_USER_FROM_CASE,
            target=assignment.case,
            payload={
                "removed_user_queue_id": str(assignment.queue.id),
                "removed_user_queue_name": assignment.queue.name,
                "removed_user_id": str(assignment.user.baseuser_ptr.id),
                "removed_user_name": removed_user_name,
            },
        )

    def delete(self, request, queue_id, assignment_id):
        try:
            assignment = CaseAssignment.objects.get(pk=assignment_id, queue_id=queue_id)
        except CaseAssignment.DoesNotExist:
            return JsonResponse(data={"error": "No such case assignment"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CaseAssignmentSerializer(assignment)
        response_data = serializer.data
        assignment.delete()
        self._create_assignment_removal_audit_entry(assignment, actor=request.user)
        return JsonResponse(data=response_data)
