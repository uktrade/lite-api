from rest_framework import serializers

from goods.models import Good


class GoodSerializer(serializers.ModelSerializer):
    description = serializers.CharField()
    is_good_controlled = serializers.BooleanField()
    is_good_end_product = serializers.BooleanField()

    class Meta:
        model = Good
        fields = ('id',
                  'description',
                  'is_good_controlled',
                  'control_code',
                  'is_good_end_product',
                  'part_number',
                  )
