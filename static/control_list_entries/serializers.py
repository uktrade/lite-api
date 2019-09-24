from rest_framework import serializers

from conf.serializers import PrimaryKeyRelatedSerializerField
from static.control_list_entries.helpers import get_parent
from static.control_list_entries.models import ControlListEntry


class ControlListEntryChildlessSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()

    def get_parent(self, instance):
        return get_parent(instance.parent)

    class Meta:
        model = ControlListEntry
        fields = '__all__'
        excludes = ['children']


class ControlListEntrySerializer(serializers.ModelSerializer):
    parent = PrimaryKeyRelatedSerializerField(queryset=ControlListEntry.objects.all(),
                                              serializer=ControlListEntryChildlessSerializer,
                                              allow_null=True)
    children = ControlListEntryChildlessSerializer(many=True, read_only=True)

    class Meta:
        model = ControlListEntry
        fields = '__all__'
