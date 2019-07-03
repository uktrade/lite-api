from rest_framework import serializers
from conf.helpers import str_to_bool
from clc_queries.models import ClcQuery
from goods.enums import GoodControlled
from goods.serializers import GoodSerializer


class ClcQuerySerializer(serializers.ModelSerializer):
    good = GoodSerializer(read_only=True)

    class Meta:
        model = ClcQuery
        fields = (
            'id',
            'details',
            'good',
            'status')
