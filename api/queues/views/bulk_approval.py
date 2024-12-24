from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import CreateAPIView

from api.applications.models import StandardApplication
from api.applications.serializers.advice import BulkApprovalAdviceSerializer
from api.cases.enums import AdviceLevel, AdviceType
from api.cases.models import Advice, Case
from api.core.authentication import GovAuthentication


class BulkApprovalCreateView(CreateAPIView):
    authentication_classes = (GovAuthentication,)
    # TODO: Add permission classes
    serializer_class = BulkApprovalAdviceSerializer

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.case_ids = []

    def get_advice_data(self, request, application):
        subjects = [("good", good_on_application.good.id) for good_on_application in application.goods.all()] + [
            (poa.party.type, poa.party.id) for poa in application.parties.all()
        ]
        return [
            {
                "level": AdviceLevel.USER,
                "type": AdviceType.APPROVE,
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
        return JsonResponse(
            {},
            status=status.HTTP_201_CREATED,
        )
