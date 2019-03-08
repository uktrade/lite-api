from rest_framework import serializers
from control_codes.models import ControlCode


class ControlCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlCode
        fields = ('id',
                  'name',
                  'description')
