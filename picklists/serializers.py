from lite_content.lite_api import strings
from rest_framework.fields import CharField, SerializerMethodField, UUIDField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from api.conf.serializers import KeyValueChoiceField
from picklists.enums import PicklistType, PickListStatus
from picklists.models import PicklistItem
from api.teams.models import Team
from api.teams.serializers import TeamReadOnlySerializer


class TinyPicklistSerializer(ModelSerializer):
    id = UUIDField(read_only=True)
    name = CharField(read_only=True)
    text = CharField(read_only=True)

    class Meta:
        model = PicklistItem
        fields = (
            "id",
            "name",
            "text",
            "updated_at",
        )


class PicklistListSerializer(TinyPicklistSerializer):
    type = KeyValueChoiceField(choices=PicklistType.choices, read_only=True)
    status = KeyValueChoiceField(choices=PickListStatus.choices, read_only=True)
    team = TeamReadOnlySerializer(read_only=True)

    class Meta:
        model = PicklistItem
        fields = TinyPicklistSerializer.Meta.fields + ("team", "type", "status",)


class PicklistUpdateCreateSerializer(ModelSerializer):
    name = CharField(allow_blank=False, required=True, error_messages={"blank": strings.Picklists.BLANK_NAME},)
    text = CharField(
        allow_blank=False, max_length=5000, required=True, error_messages={"blank": strings.Picklists.BLANK_TEXT},
    )
    type = KeyValueChoiceField(
        choices=PicklistType.choices,
        required=True,
        error_messages={"invalid_choice": strings.Picklists.BLANK_TYPE},
        allow_null=False,
        allow_blank=False,
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
