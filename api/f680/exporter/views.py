from django.db import transaction
from django.utils import timezone

from rest_framework.decorators import action
from rest_framework.response import Response

from api.core import viewsets
from api.core.context_processors import (
    CaseTypeSerializerContextProcessor,
    draft_status_serializer_context_processor,
    organisation_serializer_context_processor,
)
from api.cases.enums import CaseTypeEnum
from api.cases.celery_tasks import get_application_target_sla
from api.cases.models import CaseQueueMovement
from api.core.authentication import ExporterAuthentication
from api.organisations.filters import CurrentExporterUserOrganisationFilter
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from lite_routing.routing_rules_internal.flagging_engine import apply_flagging_rules_to_case
from lite_routing.routing_rules_internal.routing_engine import run_routing_rules

from api.f680.models import F680Application
from api.f680.exporter.serializers import (
    F680ApplicationSerializer,
    SubmittedApplicationJSONSerializer,
    FoiDeclarationSerializer,
)
from api.f680.exporter.filters import DraftApplicationFilter


class F680ApplicationViewSet(viewsets.ModelViewSet):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = F680ApplicationSerializer
    serializer_context_processors = (
        CaseTypeSerializerContextProcessor(CaseTypeEnum.F680.id),
        draft_status_serializer_context_processor,
        organisation_serializer_context_processor,
    )
    queryset = F680Application.objects.all()
    lookup_url_kwarg = "f680_application_id"
    filter_backends = [CurrentExporterUserOrganisationFilter, DraftApplicationFilter]

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        serializer = F680ApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = self.get_object()

        incoming_application_name = (
            serializer.validated_data.get("application", {})
            .get("sections", {})
            .get("general_application_details", {})
            .get("fields", {})
            .get("name", {})
            .get("answer", "")
        )

        if not application.name and incoming_application_name:
            application.name = incoming_application_name
            application.save()

        return self.update(request, *args, **kwargs)

    @transaction.atomic
    @action(detail=True)
    def submit(self, request, **kwargs):
        # TODO: What follows is a lean slice of applications.views.applications.ApplicationSubmission.
        #   We should review exactly how best to structure application submission; it could be better
        #   to depend on a model method, a library utility, or something else.  We should also think about
        #   commonality with StandardApplication
        application = self.get_object()

        application_json_serializer = SubmittedApplicationJSONSerializer(data=application.application)
        application_json_serializer.is_valid(raise_exception=True)
        application_declaration_serializer = FoiDeclarationSerializer(data=request.data)
        application_declaration_serializer.is_valid(raise_exception=True)

        # TODO: some sort of validation that we have everything we need on the application -
        #   this may duplicate frontend validation in some way so needs some consideration.
        application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        application.submitted_at = timezone.now()
        application.sla_remaining_days = get_application_target_sla(application.case_type.sub_type)
        application.sla_days = 0
        application.submitted_by = request.user.exporteruser
        application.agreed_to_foi = application_declaration_serializer.data["agreed_to_foi"]
        application.foi_reason = application_declaration_serializer.data.get("foi_reason", "")

        application.save()
        application.on_submit(application_json_serializer.data)

        apply_flagging_rules_to_case(application)
        queues_assigned = run_routing_rules(application)
        for queue in queues_assigned:
            CaseQueueMovement.objects.create(
                case=application.case_ptr, queue_id=queue, created_at=application.submitted_at
            )

        serializer = self.get_serializer(application)
        return Response(serializer.data)
