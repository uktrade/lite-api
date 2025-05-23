from api.audit_trail.models import Audit
from api.core.serializers import KeyValueChoiceField
from api.survey.models import SurveyResponse
from api.teams.models import Department
from api.cases.models import CaseAssignment, EcjuQuery, DepartmentSLA
from api.goods.enums import (
    GoodControlled,
    GoodStatus,
    ItemCategory,
)
from api.goods.models import Good
from api.licences.enums import LicenceStatus
from api.licences.models import Licence
from api.organisations.models import Site
from api.queues.models import Queue
from api.staticdata.control_list_entries.serializers import ControlListEntrySerializer
from rest_framework import serializers
import api.cases.serializers as cases_serializers


class EcjuQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = EcjuQuery
        fields = "__all__"


class CaseAssignmentSerializer(cases_serializers.CaseAssignmentSerializer):
    # Like original, but with all fields
    class Meta:
        model = CaseAssignment
        fields = "__all__"


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


class DepartmentSLASerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentSLA
        fields = "__all__"


class AuditMoveCaseSerializer(serializers.ModelSerializer):
    """Serializer for serializing 'move case' audit events."""

    user = serializers.SerializerMethodField()
    case = serializers.SerializerMethodField()
    queue = serializers.SerializerMethodField()

    class Meta:
        model = Audit
        fields = ("created_at", "user", "case", "queue")

    def get_user(self, instance):
        if instance.actor:
            return instance.actor.pk
        return None

    def get_case(self, instance):
        return instance.action_object_object_id or instance.target_object_id or None

    def get_queue(self, instance):
        queue = Queue.objects.filter(name=instance.queue).first()
        if queue:
            return queue.pk
        return None


class AuditUpdatedCaseStatusSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    case = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Audit
        fields = ("created_at", "user", "case", "status")

    def get_user(self, instance):
        if instance.actor:
            return instance.actor.pk
        return None

    def get_case(self, instance):
        return instance.target_object_id or None

    def get_status(self, instance):
        status = instance.payload["status"]["new"].lower()
        return status


class AuditUpdatedLicenceStatusSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    case = serializers.SerializerMethodField()
    licence = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Audit
        fields = ("created_at", "user", "case", "licence", "status")

    def get_user(self, instance):
        if instance.actor:
            return instance.actor.pk
        return None

    def get_case(self, instance):
        return instance.target_object_id

    def get_licence(self, instance):
        return instance.action_object_object_id

    def get_status(self, instance):
        return instance.payload["status"].lower()


class AuditBulkApprovalRecommendationSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    case = serializers.SerializerMethodField()
    queue = serializers.SerializerMethodField()

    class Meta:
        model = Audit
        fields = ("id", "created_at", "user", "case", "queue")

    def get_user(self, instance):
        return instance.actor.pk

    def get_case(self, instance):
        return instance.target_object_id or None

    def get_queue(self, instance):
        return instance.payload["queue"].lower()


class AdviceDenialReasonSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    advice_id = serializers.UUIDField()
    denialreason_id = serializers.CharField()


class LicenceSerializer(serializers.ModelSerializer):
    application = serializers.SerializerMethodField()
    status = KeyValueChoiceField(choices=LicenceStatus.choices)

    class Meta:
        model = Licence
        fields = (
            "id",
            "application",
            "reference_code",
            "status",
        )
        read_only_fields = fields
        ordering = ["created_at"]

    def get_application(self, instance):
        return {"id": str(instance.case.pk)}


class SurveyResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = "__all__"


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = "__all__"


class GoodSerializer(serializers.ModelSerializer):
    control_list_entries = ControlListEntrySerializer(many=True)
    is_good_controlled = KeyValueChoiceField(choices=GoodControlled.choices)
    status = KeyValueChoiceField(choices=GoodStatus.choices)
    item_category = KeyValueChoiceField(choices=ItemCategory.choices)

    class Meta:
        model = Good
        fields = (
            "id",
            "name",
            "description",
            "part_number",
            "control_list_entries",
            "is_good_controlled",
            "status",
            "item_category",
            "is_pv_graded",
            "report_summary",
        )
