from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import CreateAPIView

from api.applications.models import StandardApplication
from api.applications.serializers.advice import BulkApprovalAdviceSerializer
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.enums import AdviceLevel, AdviceType
from api.cases.models import Case, CaseAssignment
from api.core.authentication import GovAuthentication
from api.queues.models import Queue
from api.workflow.user_queue_assignment import user_queue_assignment_workflow


class BulkApprovalCreateView(CreateAPIView):
    authentication_classes = (GovAuthentication,)
    # TODO: Add permission classes
    serializer_class = BulkApprovalAdviceSerializer

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.case_ids = []
        self.queue = Queue.objects.get(id=kwargs["pk"])

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

    def get_advice_data(self, request, application):
        subjects = [("good", good_on_application.good.id) for good_on_application in application.goods.all()] + [
            (poa.party.type, poa.party.id) for poa in application.parties.all()
        ]
        proviso = self.advice.get("proviso", "")
        advice_type = AdviceType.PROVISO if proviso else AdviceType.APPROVE
        return [
            {
                "level": AdviceLevel.USER,
                "type": advice_type,
                "case": str(application.id),
                "user": request.user,
                subject_name: str(subject_id),
                "denial_reasons": [],
                **self.advice,
            }
            for subject_name, subject_id in subjects
        ]

    def build_instances_data(self, request):
        input_data = request.data.copy()
        self.case_ids = input_data.get("case_ids", [])
        self.advice = input_data.get("advice", {})
        self.cases = Case.objects.filter(id__in=self.case_ids)
        payload = []
        applications = StandardApplication.objects.filter(id__in=self.case_ids)
        for application in applications:
            advice_data = self.get_advice_data(request, application)
            payload.extend(advice_data)

        return payload

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = self.build_instances_data(request)
        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)

        super().perform_create(serializer)

        self.move_cases_forward(request, self.cases)

        return JsonResponse(
            {},
            status=status.HTTP_201_CREATED,
        )
