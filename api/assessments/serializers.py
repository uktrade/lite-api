from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from api.applications.models import GoodOnApplication
from api.core.serializers import GoodControlReviewSerializer
from api.staticdata.report_summaries.models import ReportSummarySubject, ReportSummaryPrefix
from api.staticdata.regimes.models import RegimeEntry
from api.users.enums import UserStatuses
from api.users.models import GovUser


class UpdateListSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data):

        instance_hash = {index: instance for index, instance in enumerate(instances)}

        result = [self.child.update(instance_hash[index], attrs) for index, attrs in enumerate(validated_data)]

        return result


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
    assessed_by = PrimaryKeyRelatedField(
        required=False, allow_null=True, queryset=GovUser.objects.filter(status=UserStatuses.ACTIVE)
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
            "assessed_by",
        )
        list_serializer_class = UpdateListSerializer
