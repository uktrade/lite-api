from rest_framework import serializers

from api.staticdata.control_list_entries.models import ControlListEntry


class ControlListEntriesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlListEntry
        fields = ("rating", "text", "parent")
