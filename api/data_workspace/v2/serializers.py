from functools import wraps

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from api.applications.models import StandardApplication
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import AdviceType
from api.cases.models import Case
from api.licences.enums import LicenceDecisionType
from api.licences.models import Licence
from api.staticdata.statuses.enums import (
    CaseStatusEnum,
    CaseSubStatusIdEnum,
)


def get_original_application(obj):
    if not obj.amendment_of:
        return obj
    return get_original_application(obj.amendment_of)


class LicenceStatusSerializer(serializers.Serializer):
    name = serializers.CharField(source="*")


class LicenceDecisionTypeSerializer(serializers.Serializer):
    name = serializers.CharField(source="*")


class SIELApplicationSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    class Meta:
        model = StandardApplication
        fields = ("id", "status")

    def get_id(self, application):
        return get_original_application(application).pk


class SIELLicenceSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Licence
        fields = (
            "id",
            "reference_code",
            "status",
        )

    def get_status(self, licence):
        return licence.status


def decision_type_checker(decision_type):
    def _decision_type_check(func):
        @wraps(func)
        def wrapper(application, case_audit_logs):
            decision_made_at = func(application, case_audit_logs)
            if not decision_made_at:
                return None
            return decision_type, decision_made_at

        return wrapper

    return _decision_type_check


@decision_type_checker(LicenceDecisionType.WITHDRAWN)
def withdrawn_check(application, case_audit_logs):
    if application.status.status != CaseStatusEnum.WITHDRAWN:
        return

    withdrawn_audit_logs = case_audit_logs.filter(
        payload__status__new__in=["withdrawn", "Withdrawn"],
        verb=AuditType.UPDATED_STATUS,
    )
    audit = withdrawn_audit_logs.latest("created_at")

    return audit.created_at


@decision_type_checker(LicenceDecisionType.NLR)
def nlr_check(application, case_audit_logs):
    if application.status.status != CaseStatusEnum.FINALISED:
        return

    if application.sub_status is not None:
        return

    final_recommendation_audit_logs = case_audit_logs.filter(
        payload__decision=AdviceType.NO_LICENCE_REQUIRED,
        verb=AuditType.CREATED_FINAL_RECOMMENDATION,
    )
    if final_recommendation_audit_logs.exists():
        audit = final_recommendation_audit_logs.latest("created_at")
        return audit.created_at

    nlr_letter_audit_logs = case_audit_logs.filter(
        payload__template="No licence required letter template",
        verb=AuditType.GENERATE_CASE_DOCUMENT,
    )
    if nlr_letter_audit_logs.exists():
        audit = nlr_letter_audit_logs.latest("created_at")
        return audit.created_at


@decision_type_checker(LicenceDecisionType.ISSUED)
def issued_check(application, case_audit_logs):
    if application.status.status != CaseStatusEnum.FINALISED:
        return

    if application.sub_status is None:
        issued_audit_logs = case_audit_logs.filter(
            payload__status="issued",
            verb=AuditType.LICENCE_UPDATED_STATUS,
        )
        if issued_audit_logs.exists():
            audit = issued_audit_logs.latest("created_at")
            return audit.created_at

        application_granted_audit_logs = case_audit_logs.filter(
            verb=AuditType.GRANTED_APPLICATION,
        )
        if application_granted_audit_logs.exists():
            audit = application_granted_audit_logs.latest("created_at")
            return audit.created_at

        return

    if str(application.sub_status.pk) != CaseSubStatusIdEnum.FINALISED__APPROVED:
        return

    issued_audit_logs = case_audit_logs.filter(
        payload__status="issued",
        verb=AuditType.LICENCE_UPDATED_STATUS,
    )
    audit = issued_audit_logs.latest("created_at")
    return audit.created_at


@decision_type_checker(LicenceDecisionType.REFUSED)
def refused_check(application, case_audit_logs):
    if application.status.status != CaseStatusEnum.FINALISED:
        return

    if application.sub_status is None:
        final_recommendation_audit_logs = case_audit_logs.filter(
            payload__decision=AdviceType.REFUSE,
            verb=AuditType.CREATED_FINAL_RECOMMENDATION,
        )
        if final_recommendation_audit_logs.exists():
            audit = final_recommendation_audit_logs.latest("created_at")
            return audit.created_at

        refusal_letter_generated_audit_logs = case_audit_logs.filter(
            payload__template="Refusal letter template",
            verb=AuditType.GENERATE_CASE_DOCUMENT,
        )
        if refusal_letter_generated_audit_logs.exists():
            audit = refusal_letter_generated_audit_logs.latest("created_at")
            return audit.created_at

        return

    if str(application.sub_status.pk) != CaseSubStatusIdEnum.FINALISED__REFUSED:
        return

    final_recommendation_audit_logs = case_audit_logs.filter(
        payload__decision=AdviceType.REFUSE,
        verb=AuditType.CREATED_FINAL_RECOMMENDATION,
    )
    audit = final_recommendation_audit_logs.latest("created_at")

    return audit.created_at


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
        else:
            raise ValueError(f"Cannot determine type of licence decision for application {application.reference_code}")


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

    def to_representation(self, application):
        return super().to_representation(LicenceDecision(application))

    def get_decision(self, licence_decision):
        return licence_decision.type

    def get_decision_made_at(self, licence_decision):
        return licence_decision.decision_made_at
