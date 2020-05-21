from rest_framework import serializers


class ControlListEntrySerializer(serializers.Serializer):
    rating = serializers.CharField(read_only=True)
    text = serializers.CharField(read_only=True)


class ControlListEntrySerializerWithLinks(ControlListEntrySerializer):
    parent = ControlListEntrySerializer(read_only=True)
    children = ControlListEntrySerializer(many=True, read_only=True)
    category = serializers.CharField()
