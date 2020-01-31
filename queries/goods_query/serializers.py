from rest_framework import serializers

from conf.serializers import PrimaryKeyRelatedSerializerField, KeyValueChoiceField
from goods.enums import PvGrading
from goods.models import PvGradingDetails
from goods.serializers import GoodWithFlagsSerializer
from organisations.models import Organisation
from organisations.serializers import TinyOrganisationViewSerializer
from queries.goods_query.models import GoodsQuery
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum
from users.libraries.notifications import (
    get_exporter_user_notification_total_count,
    get_exporter_user_notification_individual_count,
)


class GoodsQuerySerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedSerializerField(
        queryset=Organisation.objects.all(), serializer=TinyOrganisationViewSerializer
    )
    good = GoodWithFlagsSerializer(read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = GoodsQuery
        fields = (
            "id",
            "clc_raised_reasons",
            "pv_grading_raised_reasons",
            "good",
            "submitted_at",
            "organisation",
            "status",
            "clc_responded",
            "pv_grading_responded",
        )

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None


class PVGradingResponseSerializer(serializers.ModelSerializer):
    grading = KeyValueChoiceField(
        choices=PvGrading.gov_choices,
        allow_null=False,
        allow_blank=False,
        required=True,
        error_messages={"invalid_choice": "Select a grading"},
    )
    prefix = serializers.CharField(allow_blank=True, allow_null=True, max_length=30)
    suffix = serializers.CharField(allow_blank=True, allow_null=True, max_length=30)

    class Meta:
        model = PvGradingDetails
        fields = (
            "id",
            "prefix",
            "grading",
            "suffix",
        )


class ExporterReadGoodQuerySerializer(serializers.ModelSerializer):
    exporter_user_notification_count = serializers.SerializerMethodField()

    class Meta:
        model = GoodsQuery
        fields = (
            "id",
            "reference_code",
            "clc_responded",
            "clc_raised_reasons",
            "pv_grading_responded",
            "pv_grading_raised_reasons",
            "exporter_user_notification_count",
        )

    def get_exporter_user_notification_count(self, instance):
        exporter_user = self.context.get("exporter_user")
        if exporter_user:
            if self.context.get("total_count"):
                return get_exporter_user_notification_total_count(exporter_user=exporter_user, case=instance)
            else:
                return get_exporter_user_notification_individual_count(exporter_user=exporter_user, case=instance)
