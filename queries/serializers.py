from rest_framework import serializers

from queries.goods_query.serializers import GoodsQuerySerializer
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from queries.end_user_advisories.serializers import EndUserAdvisoryViewSerializer
from queries.helpers import get_exporter_query
from queries.models import Query


class QueryViewSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        instance = get_exporter_query(instance.id)

        if isinstance(instance, EndUserAdvisoryQuery):
            return EndUserAdvisoryViewSerializer(instance=instance).data
        else:
            return GoodsQuerySerializer(instance=instance).data

    class Meta:
        model = Query
        fields = "__all__"
