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


def withdrawn_check(application, case_audit_logs):
    if application.status.status != CaseStatusEnum.WITHDRAWN:
        return

    withdrawn_audit_logs = case_audit_logs.filter(
        payload__status__new__in=["withdrawn", "Withdrawn"],
        verb=AuditType.UPDATED_STATUS,
    )
    audit = withdrawn_audit_logs.latest("created_at")

    return LicenceDecisionType.WITHDRAWN, audit.created_at


def nlr_check(application, case_audit_logs):
    if application.status.status != CaseStatusEnum.FINALISED:
        return

    if application.sub_status is not None:
        return

    final_recommendation_audit_logs = case_audit_logs.filter(
        payload__decision=AdviceType.NO_LICENCE_REQUIRED,
        verb=AuditType.CREATED_FINAL_RECOMMENDATION,
    )
    if not final_recommendation_audit_logs.exists():
        return

    audit = final_recommendation_audit_logs.latest("created_at")

    return LicenceDecisionType.NLR, audit.created_at


def issued_check(application, case_audit_logs):
    if application.status.status != CaseStatusEnum.FINALISED:
        return

    if application.sub_status is None:
        application_granted_audit_logs = case_audit_logs.filter(
            verb=AuditType.GRANTED_APPLICATION,
        )
        if not application_granted_audit_logs.exists():
            return

        audit = application_granted_audit_logs.latest("created_at")
        return LicenceDecisionType.ISSUED, audit.created_at

    if str(application.sub_status.pk) != CaseSubStatusIdEnum.FINALISED__APPROVED:
        return

    issued_audit_logs = case_audit_logs.filter(
        payload__status="issued",
        verb=AuditType.LICENCE_UPDATED_STATUS,
    )
    audit = issued_audit_logs.latest("created_at")
    return LicenceDecisionType.ISSUED, audit.created_at


def refused_check(application, case_audit_logs):
    if application.status.status != CaseStatusEnum.FINALISED:
        return

    if application.sub_status is None:
        return

    if str(application.sub_status.pk) != CaseSubStatusIdEnum.FINALISED__REFUSED:
        return

    final_recommendation_audit_logs = case_audit_logs.filter(
        payload__decision=AdviceType.REFUSE,
        verb=AuditType.CREATED_FINAL_RECOMMENDATION,
    )
    audit = final_recommendation_audit_logs.latest("created_at")

    return LicenceDecisionType.REFUSED, audit.created_at


class LicenceDecision:
    decision_checks = [
        withdrawn_check,
        nlr_check,
        issued_check,
        refused_check,
    ]

    def __init__(self, application):
        self.application_id = application.pk
        self.setup(application)

    def get_case_audit_logs(self, application):
        target_content_type = ContentType.objects.get_for_model(Case)
        return Audit.objects.filter(
            target_content_type=target_content_type,
            target_object_id=application.get_case().pk,
        )

    def setup(self, application):
        case_audit_logs = self.get_case_audit_logs(application)

        for decision_check in self.decision_checks:
            decision = decision_check(application, case_audit_logs)
            if decision:
                self.type, self.decision_made_at = decision
                break

        return


class LicenceDecisionSerializer(serializers.ModelSerializer):
    application_id = serializers.UUIDField()
    decision = serializers.SerializerMethodField()
    decision_made_at = serializers.SerializerMethodField()

    class Meta:
        model = StandardApplication
        fields = (
            "application_id",
            "decision",
            "decision_made_at",
        )

    def to_representation(self, instance):
        return super().to_representation(LicenceDecision(instance))

    def get_decision(self, licence_decision):
        return licence_decision.type

    def get_decision_made_at(self, licence_decision):
        return licence_decision.decision_made_at
