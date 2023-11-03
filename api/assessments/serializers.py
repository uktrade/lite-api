from django.utils import timezone
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from api.applications.models import GoodOnApplication
from api.core.serializers import GoodControlReviewSerializer
from api.flags.enums import SystemFlags
from api.goods.enums import GoodStatus
from api.staticdata.report_summaries.models import ReportSummarySubject, ReportSummaryPrefix
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.enums import UserStatuses
from api.users.models import GovUser

from lite_content.lite_api import strings


class AssessmentUpdateListSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data):

        instance_hash = {index: instance for index, instance in enumerate(instances)}

        result = [self.child.update(instance_hash[index], attrs) for index, attrs in enumerate(validated_data)]

        return result

    def validate(self, data):
        if self.instance:
            application = self.instance[0].application
            if CaseStatusEnum.is_terminal(application.status.status):
                raise serializers.ValidationError(
                    strings.Applications.Generic.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR
                )
        return data


class AssessmentSerializer(GoodControlReviewSerializer):

    regime_entries = PrimaryKeyRelatedField(
        many=True,
        queryset=RegimeEntry.objects.all(),
        required=False,  # Not required until we completely do away with the string report_summary field..
    )
    report_summary_prefix = PrimaryKeyRelatedField(
        required=False, allow_null=True, queryset=ReportSummaryPrefix.objects.all()
    )
    report_summary_subject = PrimaryKeyRelatedField(
        required=False, allow_null=True, queryset=ReportSummarySubject.objects.all()
    )

    class Meta:
        model = GoodOnApplication
        fields = (
            "control_list_entries",
            "is_good_controlled",
            "comment",
            "report_summary",
            "regime_entries",
            "report_summary_prefix",
            "report_summary_subject",
            "is_ncsc_military_information_security",
        )
        list_serializer_class = AssessmentUpdateListSerializer

    def validate(self, data):
        # If we have a report summary subject, overwrite whatever report_summary value
        # we have with the string from the subject/prefix
        if data.get("report_summary_subject"):
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

    def update(self, instance, validated_data):
        super().update(instance, validated_data)
        instance.assessed_by = validated_data["user"]
        instance.assessment_date = timezone.now()
        instance.save()

        self.update_good(instance, validated_data)

        return instance
