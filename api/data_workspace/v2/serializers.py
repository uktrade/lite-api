from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from api.applications.models import StandardApplication
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import Case
from api.licences.enums import LicenceDecisionType
from api.staticdata.statuses.enums import CaseStatusEnum


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

    def get_decision_made_at(self, application):
        if application.status.status == CaseStatusEnum.WITHDRAWN:
            target_content_type = ContentType.objects.get_for_model(Case)
            withdrawn_audit_logs = Audit.objects.filter(
                payload__status__new__in=["withdrawn", "Withdrawn"],
                target_content_type=target_content_type,
                target_object_id=application.get_case().pk,
                verb=AuditType.UPDATED_STATUS,
            )
            audit = withdrawn_audit_logs.latest("created_at")
            return audit.created_at
