from rest_framework import serializers


class ControlListEntrySerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    rating = serializers.CharField(read_only=True)
    text = serializers.CharField(read_only=True)
    is_decontrolled = serializers.BooleanField(read_only=True)


class ControlListEntrySerializerWithLinks(ControlListEntrySerializer):
    parent = ControlListEntrySerializer(read_only=True)
    children = ControlListEntrySerializer(many=True, read_only=True)
