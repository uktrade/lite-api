from rest_framework import serializers


class SearchQueueSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    case_count = serializers.IntegerField()
    team = serializers.CharField()
