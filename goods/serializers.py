from typing import Optional, Any

from rest_framework import serializers

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

    def __init__(self, instance: Optional[Any] = ..., data: Any = ..., **kwargs: Any):
        super().__init__(instance, data, **kwargs)
        if self.fields['is_good_controlled'] is True:
            self.fields['control_code'].required = True