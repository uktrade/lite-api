import logging

from django.utils import timezone
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from api.applications.models import GoodOnApplication
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.libraries.get_case import get_case
from api.core.exceptions import NotFoundError
from api.core.serializers import GoodControlReviewSerializer, PrimaryKeyRelatedSerializerField
from api.flags.enums import SystemFlags
from api.goods.enums import GoodStatus
from api.staticdata.report_summaries.models import ReportSummary, ReportSummarySubject, ReportSummaryPrefix
from api.staticdata.report_summaries.serializers import ReportSummarySerializer
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.statuses.enums import CaseStatusEnum

from lite_content.lite_api import strings

logger = logging.getLogger(__name__)


class AssessmentUpdateListSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data):
        instances_by_id = {str(instance.id): instance for instance in instances}
        validated_data_by_id = {str(data["id"]): data for data in validated_data if data.get("id")}
        instance_data_pairs = []
        for instance_id, instance in instances_by_id.items():
            instance_data_pairs.append((instance, validated_data_by_id[instance_id]))
        result = [
            self.child.update(instance, validated_update_data)
            for instance, validated_update_data in instance_data_pairs
        ]
        return result

    def validate(self, data):
        if self.instance:
            application = self.instance[0].application
            if CaseStatusEnum.is_terminal(application.status.status):
                raise serializers.ValidationError(
                    strings.Applications.Generic.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR
                )
        return data


class ReportSummaryField(PrimaryKeyRelatedSerializerField):

    def __init__(self, **kwargs):
        super().__init__(
            queryset=ReportSummary.objects.all(),
            many=kwargs.get("many"),
            serializer=ReportSummarySerializer,
            error_messages={},
            **kwargs,
        )

    def to_internal_value(self, data):
        try:
            return ReportSummary.objects.get(prefix=data["prefix"], subject=data["subject"])
        except NotFoundError:
            raise serializers.ValidationError("Report summary with given prefix and subject is not found")


class AssessmentSerializer(GoodControlReviewSerializer):

    id = serializers.UUIDField()
    regime_entries = PrimaryKeyRelatedField(
        many=True,
        queryset=RegimeEntry.objects.all(),
        required=False,
    )
    report_summary_prefix = PrimaryKeyRelatedField(
        required=False, allow_null=True, queryset=ReportSummaryPrefix.objects.all()
    )
    report_summary_subject = PrimaryKeyRelatedField(
        required=False, allow_null=True, queryset=ReportSummarySubject.objects.all()
    )
    report_summaries = ReportSummaryField(required=False, allow_null=True, many=True)

    class Meta:
        model = GoodOnApplication
        fields = (
            "id",
            "control_list_entries",
            "is_good_controlled",
            "comment",
            "report_summary",
            "regime_entries",
            "report_summary_prefix",
            "report_summary_subject",
            "report_summaries",
            "is_ncsc_military_information_security",
        )
        list_serializer_class = AssessmentUpdateListSerializer

    def validate(self, data):
        if "is_good_controlled" in data and data["is_good_controlled"] in (False, None):
            # Goods that are not controlled should have a blank report summary
            data["report_summary"] = None
            data["report_summary_prefix"] = None
            data["report_summary_subject"] = None
        elif (
            data.get("report_summary") is not None
            and data.get("report_summary_subject") is None
            and data.get("report_summary_prefix") is None
        ):
            # Legacy GoodOnApplications only have a report_summary populated, not the subject/prefix
            # - Once report_summary is removed, remove this check
            logger.info(
                "GoodOnApplication %s is legacy format: has report_summary but no report_summary_subject or report_summary_prefix",
                data.get("id"),
            )
        elif "report_summary_subject" in data:
            if data["report_summary_subject"] is None:
                raise serializers.ValidationError({"report_summary_subject": strings.Picklists.REQUIRED_REPORT_SUMMARY})

            if data.get("report_summary_prefix"):
                data["report_summary"] = f"{data['report_summary_prefix'].name} {data['report_summary_subject'].name}"
            else:
                data["report_summary"] = data["report_summary_subject"].name

        return data

    def update_good(self, instance, validated_data):
        good = instance.good
        # Add control entries to a verified good
        if good.status == GoodStatus.VERIFIED:
            good.control_list_entries.add(*validated_data["control_list_entries"])
        # Overwrite control entries for a previously unverified good
        else:
            good.status = GoodStatus.VERIFIED
            good.control_list_entries.set(validated_data["control_list_entries"])
            good.flags.remove(SystemFlags.GOOD_NOT_YET_VERIFIED_ID)

        # Set report summary fields on the good
        good.report_summary = validated_data.get("report_summary", instance.report_summary)
        if validated_data.get("report_summary_prefix", None):
            good.report_summary_prefix = validated_data["report_summary_prefix"]
        if validated_data.get("report_summary_subject", None):
            good.report_summary_subject = validated_data["report_summary_subject"]

        good.save()

    def emit_audit_entry(self, instance, validated_data, old_values):
        case = get_case(instance.application_id, select_related=["status"])
        default_control = [strings.Goods.GOOD_NO_CONTROL_CODE]
        default_regimes = ["No regimes"]
        new_control_list_entries = [item.rating for item in validated_data["control_list_entries"]]
        new_regime_entries = [regime_entry.name for regime_entry in validated_data.get("regime_entries", [])]
        audit_trail_service.create(
            actor=validated_data["user"],
            verb=AuditType.PRODUCT_REVIEWED,
            action_object=instance,
            target=case,
            payload={
                "line_no": validated_data["line_numbers"][instance.id],
                "good_name": instance.name,
                "new_control_list_entry": new_control_list_entries or default_control,
                "old_control_list_entry": old_values["control_list_entry"] or default_control,
                "old_is_good_controlled": "Yes" if old_values["is_good_controlled"] else "No",
                "new_is_good_controlled": "Yes" if validated_data["is_good_controlled"] else "No",
                "old_report_summary": old_values["report_summary"],
                "report_summary": instance.report_summary,
                "additional_text": validated_data["comment"],
                "old_regime_entries": old_values["regime_entries"] or default_regimes,
                "new_regime_entries": new_regime_entries or default_regimes,
            },
        )

    def get_old_values_for_audit(self, instance):
        return {
            "control_list_entry": [cle.rating for cle in instance.control_list_entries.all()],
            "is_good_controlled": instance.is_good_controlled,
            "report_summary": instance.report_summary,
            "regime_entries": [regime_entry.name for regime_entry in instance.regime_entries.all()],
        }

    def update(self, instance, validated_data):
        old_values = self.get_old_values_for_audit(instance)
        super().update(instance, validated_data)
        instance.assessed_by = validated_data["user"]
        instance.assessment_date = timezone.now()
        instance.save()

        self.update_good(instance, validated_data)
        self.emit_audit_entry(instance, validated_data, old_values)

        return instance
