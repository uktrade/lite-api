from api.audit_trail.enums import AuditType
from api.cases.models import Case
from api.staticdata.statuses.libraries.get_case_status import get_status_value_from_case_status_enum
from api.staticdata.statuses.models import CaseStatus
from api.applications.models import ApplicationDocument
from api.documents.libraries.process_document import process_document
from api.audit_trail import service as audit_trail_service

from rest_framework import serializers

from api.staticdata.statuses.enums import CaseStatusEnum


class ApplicationChangeStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=CaseStatusEnum.all())
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)


class ApplicationStatusSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = CaseStatus
        fields = ("status", "status_display")

    def get_status_display(self, obj):
        return get_status_value_from_case_status_enum(obj.status)


class CaseAmendmentSerializer(serializers.Serializer):
    status = serializers.SerializerMethodField()
    ecju_query_count = serializers.SerializerMethodField()
    reference_code = serializers.CharField()
    submitted_at = serializers.DateTimeField()
    id = serializers.UUIDField()
    status = ApplicationStatusSerializer()

    def get_ecju_query_count(self, instance):
        return instance.case_ecju_query.all().count()


class ApplicationHistorySerializer(serializers.ModelSerializer):
    amendment_history = serializers.SerializerMethodField()

    def get_amendment_history(self, instance):
        amendments = []
        case_amended = instance

        # Go backwards through amendment chain until we find the original case
        while case_amended.superseded_by:
            case_amended = case_amended.superseded_by

        # Travel forwards in amendment chain to find the latest amended case
        while case_amended:
            case_amended_data = CaseAmendmentSerializer(case_amended).data
            amendments.append(case_amended_data)
            case_amended = case_amended.amendment_of
        return amendments

    class Meta:
        model = Case
        fields = ("id", "reference_code", "amendment_history")


class ExporterApplicationDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApplicationDocument
        fields = "__all__"

    def create(self, validated_data):
        # This rich is moved here to avoid heavy helpers in the view keeping view as simple
        # TODO move these to models
        document = super().create(validated_data)
        document.save()
        process_document(document)
        audit_trail_service.create(
            actor=self.context["request"].user,
            verb=AuditType.UPLOAD_APPLICATION_DOCUMENT,
            target=validated_data["application"].get_case(),
            payload={"file_name": validated_data["name"]},
        )
        return document
