from rest_framework import serializers

from case_types.models import CaseType


class CaseTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CaseType
        fields = ['id', 'name']
