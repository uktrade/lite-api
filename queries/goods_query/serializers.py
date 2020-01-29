from rest_framework import serializers

from conf.serializers import PrimaryKeyRelatedSerializerField, KeyValueChoiceField
from goods.enums import PvGrading
from goods.models import PvGradingDetails
from goods.serializers import GoodWithFlagsSerializer
from organisations.models import Organisation
from organisations.serializers import TinyOrganisationViewSerializer
from queries.goods_query.models import GoodsQuery
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum


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
    prefix = serializers.CharField(allow_blank=True, allow_null=True)
    suffix = serializers.CharField(allow_blank=True, allow_null=True)

    class Meta:
        model = PvGradingDetails
        fields = (
            "id",
            "prefix",
            "grading",
            "suffix",
        )
