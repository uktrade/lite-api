from rest_framework import serializers

from conf.helpers import str_to_bool
from goods.models import Good


class GoodSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=280)
    is_good_controlled = serializers.BooleanField()
    control_code = serializers.CharField(required=False)
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

    def __init__(self, *args, **kwargs):
        super(GoodSerializer, self).__init__(*args, **kwargs)

        if str_to_bool(self.get_initial().get('is_good_controlled')) is True:
            self.fields['control_code'] = serializers.CharField(required=True)
