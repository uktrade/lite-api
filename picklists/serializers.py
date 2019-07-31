from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from content_strings.strings import get_string
from picklists.enums import PicklistType, PickListStatus
from picklists.models import PicklistItem
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
    team_name = serializers.SerializerMethodField()

    def get_team_name(self, instance):
        return instance.team.name

    class Meta:
        model = PicklistItem
        fields = ('id',
                  'team',
                  'name',
                  'text',
                  'type',
                  'status',
                  'team_name')

