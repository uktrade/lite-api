from rest_framework import serializers


class CaseViewBaseSerializer(serializers.Serializer):
    reference_code = serializers.CharField()
