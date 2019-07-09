from rest_framework import serializers
from clc_queries.models import ClcQuery
from goods.serializers import GoodSerializer


class ClcQuerySerializer(serializers.ModelSerializer):
    good = GoodSerializer(read_only=True)
    organisation_name = serializers.SerializerMethodField()

    class Meta:
        model = ClcQuery
        fields = (
            'id',
            'details',
            'good',
            'status',
            'organisation_name')

    def get_organisation_name(self, instance):
        return instance.good.organisation.name