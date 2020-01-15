from rest_framework import serializers

from conf.serializers import PrimaryKeyRelatedSerializerField
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
        )

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None
