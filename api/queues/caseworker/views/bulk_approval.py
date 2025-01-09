from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import CreateAPIView

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import AdviceLevel, AdviceType
from api.core.authentication import GovAuthentication
from api.core.permissions import CanCaseworkerBulkApprove
from api.queues.caseworker.serializers import BulkApprovalSerializer
from api.queues.models import Queue


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

    def move_cases_forward(self, request, cases):
        for case in cases:
            case.move_case_forward(self.queue, request.user)

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
