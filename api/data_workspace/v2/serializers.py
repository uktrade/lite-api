from rest_framework import serializers


from api.audit_trail.models import Audit
from api.applications.models import StandardApplication
from api.cases.models import EcjuQuery
from api.staticdata.statuses.enums import CaseStatusEnum


def get_original_application(obj):
    if not obj.amendment_of:
        return obj
    return get_original_application(obj.amendment_of)


def get_last_application(obj):
    if not obj.superseded_by:
        return obj
    return get_last_application(obj.superseded_by)


class ApplicationSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(required=False)
    status = serializers.SerializerMethodField(required=False)

    class Meta:
        model = StandardApplication
        fields = ("id", "status")

    def get_id(self, application):
        application = get_original_application(application)
        return application.pk

    def get_status(self, application):
        return application.status.status


class RFISerializer(serializers.ModelSerializer):
    application_id = serializers.SerializerMethodField(required=False)
    closed_at = serializers.SerializerMethodField(required=False)

    class Meta:
        model = EcjuQuery
        fields = (
            "id",
            "application_id",
            "created_at",
            "closed_at",
        )

    def get_application_id(self, rfi):
        return get_original_application(rfi.case).pk

    def get_closed_at(self, rfi):
        return rfi.responded_at


class StatusChangeSerializer(serializers.ModelSerializer):
    application_id = serializers.SerializerMethodField(required=False)
    changed_at = serializers.SerializerMethodField(required=False)
    status = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Audit
        fields = (
            "id",
            "application_id",
            "changed_at",
            "status",
        )

    def get_application_id(self, audit):
        application = get_original_application(audit.target)
        return application.pk

    def get_changed_at(self, audit):
        return audit.created_at

    def get_status(self, audit):
        status = audit.payload["status"]["new"].lower().replace(" ", "_").replace("-", "")
        if status not in CaseStatusEnum.all():
            raise ValueError(f"Unknown status {status}")
        return status


class StatusSerializer(serializers.Serializer):
    name = serializers.SerializerMethodField(required=False)
    is_terminal = serializers.SerializerMethodField(required=False)
    is_closed = serializers.SerializerMethodField(required=False)

    def get_name(self, status_name):
        return status_name

    def get_is_terminal(self, status_name):
        return CaseStatusEnum.is_terminal(status_name)

    def get_is_closed(self, status_name):
        return CaseStatusEnum.is_closed(status_name)


class NonWorkingDaySerializer(serializers.Serializer):
    date = serializers.SerializerMethodField(required=False)
    type = serializers.SerializerMethodField(required=False)

    def get_date(self, date_and_type):
        date, _ = date_and_type
        return date

    def get_type(self, date_and_type):
        _, type = date_and_type
        return type
