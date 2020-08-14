from rest_framework import serializers

from api.queries.goods_query.serializers import GoodsQuerySerializer
from api.queries.end_user_advisories.models import EndUserAdvisoryQuery
from api.queries.end_user_advisories.serializers import EndUserAdvisoryViewSerializer
from api.queries.helpers import get_exporter_query
from api.queries.models import Query


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
