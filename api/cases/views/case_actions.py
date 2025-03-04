from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.libraries.get_case import get_case
from api.cases.models import CaseAssignment, CaseQueueMovement
from api.core.authentication import GovAuthentication
from lite_content.lite_api.strings import Cases
from api.queues.models import Queue
from api.queues.serializers import TinyQueueSerializer
from api.workflow.user_queue_assignment import user_queue_assignment_workflow

from lite_routing.routing_rules_internal.routing_engine import run_routing_rules


class AssignedQueues(APIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = TinyQueueSerializer

    def get(self, request, pk):
        # Get all queues where this user is assigned to this case
        queues = Queue.objects.filter(case_assignments__user=request.user.pk, case_assignments__case=pk)
        serializer = TinyQueueSerializer(queues, many=True)
        return JsonResponse(data={"queues": serializer.data}, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, pk):
        queues = request.data.get("queues")
        note = request.data.get("note")

        if queues:
            queue_names = []
            assignments = (
                CaseAssignment.objects.select_related("queue")
                .filter(user=request.user.govuser, case__id=pk, queue__id__in=queues)
                .order_by("queue__name")
            )
            case = get_case(pk)

            if assignments:
                queues = [assignment.queue for assignment in assignments]
                queue_names = [queue.name for queue in queues]
                assignments.delete()
                user_queue_assignment_workflow(queues, case)
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.UNASSIGNED_QUEUES,
                    target=case,
                    payload={"queues": queue_names, "additional_text": note},
                )
            else:
                # When users click done without queue assignments
                # Only a single queue ID can be passed
                if len(queues) != 1:
                    return JsonResponse(
                        data={"errors": {"queues": [Cases.UnassignQueues.NOT_ASSIGNED_MULTIPLE_QUEUES]}},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # Check queue belongs to that users team
                queues = Queue.objects.filter(id=queues[0], team=request.user.govuser.team)
                if not queues.exists():
                    return JsonResponse(
                        data={"errors": {"queues": [Cases.UnassignQueues.INVALID_TEAM]}},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user_queue_assignment_workflow(queues, case)
                audit_trail_service.create(
                    actor=request.user, verb=AuditType.UNASSIGNED, target=case, payload={"additional_text": note}
                )

            # Record queue unassigned date
            for queue in queues:
                CaseQueueMovement.record_exit_date(case, queue)

            return JsonResponse(data={"queues_removed": queue_names}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(
                data={"errors": {"queues": [Cases.UnassignQueues.NO_QUEUES]}}, status=status.HTTP_400_BAD_REQUEST
            )


class RerunRoutingRules(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request, pk):
        """
        Reruns routing rules against a given case, in turn removing all existing queues, and user assignments,
            and starting again from scratch on the given status
        Audits who requests the rules to be rerun
        """
        case = get_case(pk)

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.RERUN_ROUTING_RULES,
            target=case,
        )

        run_routing_rules(case)

        return JsonResponse(data={}, status=status.HTTP_200_OK)
