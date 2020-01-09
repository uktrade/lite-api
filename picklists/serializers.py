from lite_content.lite_api import strings
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from conf.serializers import KeyValueChoiceField
from picklists.enums import PicklistType, PickListStatus
from picklists.models import PicklistItem
from teams.models import Team


class PicklistSerializer(ModelSerializer):
    name = CharField(allow_blank=False, required=True, error_messages={"blank": strings.Picklists.BLANK_NAME},)
    text = CharField(
        allow_blank=False, max_length=5000, required=True, error_messages={"blank": strings.Picklists.BLANK_TEXT},
    )
    type = KeyValueChoiceField(
        choices=PicklistType.choices, required=True, error_messages={"invalid_choice": strings.Picklists.BLANK_TYPE},
    )
    status = KeyValueChoiceField(
        choices=PickListStatus.choices, error_messages={"invalid_choice": strings.Picklists.BLANK_STATUS},
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
            "updated_at",
        )
