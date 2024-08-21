from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from api.applications.models import StandardApplication
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import AdviceType
from api.cases.models import Case
from api.licences.enums import LicenceDecisionType
from api.staticdata.statuses.enums import (
    CaseStatusEnum,
    CaseSubStatusIdEnum,
)


# def get_original_application(obj):
#     if not obj.amendment_of:
#         return obj
#     return get_original_application(obj.amendment_of)


class LicenceStatusSerializer(serializers.Serializer):
    name = serializers.CharField(source="*")


class LicenceDecisionTypeSerializer(serializers.Serializer):
    name = serializers.CharField(source="*")


class SIELApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardApplication
        fields = ("id", "status")


class LicenceDecisionSerializer(serializers.ModelSerializer):
    application_id = serializers.UUIDField(source="id")
    decision = serializers.SerializerMethodField()
    decision_made_at = serializers.SerializerMethodField()

    class Meta:
        model = StandardApplication
        fields = (
            "application_id",
            "decision",
            "decision_made_at",
        )

    def get_decision(self, application):
        if application.status.status == CaseStatusEnum.WITHDRAWN:
            return LicenceDecisionType.WITHDRAWN

        if application.status.status == CaseStatusEnum.FINALISED and application.sub_status is None:
            target_content_type = ContentType.objects.get_for_model(Case)
            case_audit_logs = Audit.objects.filter(
                target_content_type=target_content_type,
                target_object_id=application.get_case().pk,
            )
            final_recommendation_audit_logs = case_audit_logs.filter(
                payload__decision=AdviceType.NO_LICENCE_REQUIRED,
                verb=AuditType.CREATED_FINAL_RECOMMENDATION,
            )
            if final_recommendation_audit_logs.exists():
                return LicenceDecisionType.NLR

        if (
            application.status.status == CaseStatusEnum.FINALISED
            and str(application.sub_status.pk) == CaseSubStatusIdEnum.FINALISED__APPROVED
        ):
            return LicenceDecisionType.ISSUED

        if (
            application.status.status == CaseStatusEnum.FINALISED
            and str(application.sub_status.pk) == CaseSubStatusIdEnum.FINALISED__REFUSED
        ):
            return LicenceDecisionType.REFUSED

    def get_decision_made_at(self, application):
        target_content_type = ContentType.objects.get_for_model(Case)
        case_audit_logs = Audit.objects.filter(
            target_content_type=target_content_type,
            target_object_id=application.get_case().pk,
        )

        if application.status.status == CaseStatusEnum.WITHDRAWN:
            withdrawn_audit_logs = case_audit_logs.filter(
                payload__status__new__in=["withdrawn", "Withdrawn"],
                verb=AuditType.UPDATED_STATUS,
            )
            audit = withdrawn_audit_logs.latest("created_at")
            return audit.created_at

        if application.status.status == CaseStatusEnum.FINALISED and application.sub_status is None:
            target_content_type = ContentType.objects.get_for_model(Case)
            case_audit_logs = Audit.objects.filter(
                target_content_type=target_content_type,
                target_object_id=application.get_case().pk,
            )
            final_recommendation_audit_logs = case_audit_logs.filter(
                payload__decision=AdviceType.NO_LICENCE_REQUIRED,
                verb=AuditType.CREATED_FINAL_RECOMMENDATION,
            )
            if final_recommendation_audit_logs.exists():
                audit = final_recommendation_audit_logs.latest("created_at")
                return audit.created_at

        if (
            application.status.status == CaseStatusEnum.FINALISED
            and str(application.sub_status.pk) == CaseSubStatusIdEnum.FINALISED__APPROVED
        ):
            issued_audit_logs = case_audit_logs.filter(
                payload__status="issued",
                verb=AuditType.LICENCE_UPDATED_STATUS,
            )
            audit = issued_audit_logs.latest("created_at")
            return audit.created_at

        if (
            application.status.status == CaseStatusEnum.FINALISED
            and str(application.sub_status.pk) == CaseSubStatusIdEnum.FINALISED__REFUSED
        ):
            issued_audit_logs = case_audit_logs.filter(
                payload__decision=AdviceType.REFUSE,
                verb=AuditType.CREATED_FINAL_RECOMMENDATION,
            )
            audit = issued_audit_logs.latest("created_at")
            return audit.created_at
