from rest_framework import serializers


class ControlListEntrySerializer(serializers.Serializer):
    rating = serializers.CharField(read_only=True)
    text = serializers.CharField(read_only=True)
