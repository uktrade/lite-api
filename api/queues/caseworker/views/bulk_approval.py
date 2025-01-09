from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import CreateAPIView

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import AdviceLevel, AdviceType
from api.cases.models import CaseAssignment
from api.core.authentication import GovAuthentication
from api.core.permissions import CanCaseworkerBulkApprove
from api.queues.caseworker.serializers import BulkApprovalSerializer
from api.queues.models import Queue
from api.workflow.user_queue_assignment import user_queue_assignment_workflow


class BulkApprovalCreateView(CreateAPIView):
    authentication_classes = (GovAuthentication,)
    permission_classes = [CanCaseworkerBulkApprove]
    serializer_class = BulkApprovalSerializer

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.case_ids = []
        self.queue = Queue.objects.get(id=kwargs["pk"])

    def get_serializer_context(self):
        context = super().get_serializer_context()

        context["user"] = self.request.user
        return context

    def move_case_forward(self, request, case):
        assignments = (
            CaseAssignment.objects.select_related("queue").filter(case=case, queue=self.queue).order_by("queue__name")
        )

        # Unassign existing case advisors to be able to move forward
        if assignments:
            assignments.delete()

        # Run routing rules and move the case forward
        user_queue_assignment_workflow([self.queue], case)

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.UNASSIGNED_QUEUES,
            target=case,
            payload={"queues": [self.queue.name], "additional_text": ""},
        )

    def move_cases_forward(self, request, cases):
        for case in cases:
            self.move_case_forward(request, case)

    def create_audit_events(self, request, cases):
        case_references = [case.reference_code for case in cases]
        events = [
            Audit(
                actor=request.user.govuser,
                verb=AuditType.CREATE_BULK_APPROVAL_RECOMMENDATION,
                target=case,
                payload={
                    "case_references": case_references,
                    "decision": AdviceType.APPROVE,
                    "level": AdviceLevel.USER,
                    "queue": self.queue.name,
                    "team_id": str(request.user.govuser.team_id),
                    "count": len(cases),
                },
            )
            for case in cases
        ]

        Audit.objects.bulk_create(events)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        super().perform_create(serializer)

        cases = serializer.validated_data["cases"]

        self.create_audit_events(request, cases)

        self.move_cases_forward(request, cases)

        return JsonResponse(
            {"cases": [case.reference_code for case in cases]},
            status=status.HTTP_201_CREATED,
        )
