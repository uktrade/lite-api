from rest_framework import serializers


class LicenceStatusSerializer(serializers.Serializer):
    name = serializers.CharField(source="*")
