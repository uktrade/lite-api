from rest_framework import views
from rest_framework import status
from django.http import JsonResponse

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.models import CaseAssignment
from api.cases.serializers import CaseAssignmentSerializer
from api.core.authentication import GovAuthentication


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

    def delete(self, request, case_id, assignment_id):
        try:
            assignment = CaseAssignment.objects.get(pk=assignment_id, case_id=case_id)
        except CaseAssignment.DoesNotExist:
            return JsonResponse(data={"error": "No such case assignment"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CaseAssignmentSerializer(assignment)
        response_data = serializer.data
        assignment.delete()
        self._create_assignment_removal_audit_entry(assignment, actor=request.user)
        return JsonResponse(data=response_data)
