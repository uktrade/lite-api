from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from content_strings.strings import get_string
from picklist_items.enums import PicklistType, PickListStatus
from picklist_items.models import PicklistItem
from teams.models import Team


class PicklistSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedField(queryset=Team.objects.all())

    name = serializers.CharField(allow_blank=False,
                                 error_messages={'blank': get_string('picklist_items.error_messages.blank_name')})

    text = serializers.CharField(allow_blank=False,
                                 max_length=5000,
                                 error_messages={'blank': get_string('picklist_items.error_messages.blank_text')})

    type = serializers.ChoiceField(choices=PicklistType.choices,
                                   error_messages={'invalid_choice': get_string('picklist_items.error_messages.blank_type')})

    status = serializers.ChoiceField(choices=PickListStatus.choices,
                                     error_messages={'invalid_choice': get_string('picklist_items.error_messages.blank_status')})

    def get_team_name(self, instance):
        return instance.team.name

    class Meta:
        model = PicklistItem
        fields = ('id',
                  'team',
                  'name',
                  'text',
                  'type',
                  'status')

    def validate_name(self, attrs):
        return attrs

    def validate_text(self, attrs):
        return attrs

    def validate_type(self, attrs):
        return attrs

    def validate_status(self, attrs):
        return attrs

    def validate_team(self, attrs):
        return attrs
