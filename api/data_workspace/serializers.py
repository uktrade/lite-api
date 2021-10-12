from api.audit_trail.models import Audit
from api.teams.models import Department
from api.cases.models import CaseAssignment, EcjuQuery, DepartmentSLA
from api.queues.models import Queue

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
        status = instance.payload["status"]["new"]
        return status
