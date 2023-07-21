from rest_framework import serializers

from api.queries.end_user_advisories.serializers import EndUserAdvisoryViewSerializer
from api.queries.helpers import get_exporter_query
from api.queries.models import Query


class QueryViewSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        instance = get_exporter_query(instance.id)

        return EndUserAdvisoryViewSerializer(instance=instance).data

    class Meta:
        model = Query
        fields = "__all__"
