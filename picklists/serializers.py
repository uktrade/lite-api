from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from conf.serializers import KeyValueChoiceField
from content_strings.strings import get_string
from picklists.enums import PicklistType, PickListStatus
from picklists.models import PicklistItem
from teams.models import Team


class PicklistSerializer(ModelSerializer):
    name = CharField(
        allow_blank=False,
        required=True,
        error_messages={"blank": get_string("picklist_items.error_messages.blank_name")},
    )
    text = CharField(
        allow_blank=False,
        max_length=5000,
        required=True,
        error_messages={"blank": get_string("picklist_items.error_messages.blank_text")},
    )
    type = KeyValueChoiceField(
        choices=PicklistType.choices,
        required=True,
        error_messages={"invalid_choice": get_string("picklist_items.error_messages.blank_type")},
    )
    status = KeyValueChoiceField(
        choices=PickListStatus.choices,
        error_messages={"invalid_choice": get_string("picklist_items.error_messages.blank_status")},
    )
    team = PrimaryKeyRelatedField(queryset=Team.objects.all())
    team_name = SerializerMethodField()

    def get_team_name(self, instance):
        return instance.team.name

    class Meta:
        model = PicklistItem
        fields = (
            "id",
            "team",
            "name",
            "text",
            "type",
            "status",
            "team_name",
            "last_modified_at",
        )
