import lite_content.lite_api.teams
from lite_content.lite_api import strings
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from teams.models import Team


class TeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=50,
        validators=[
            UniqueValidator(queryset=Team.objects.all(), lookup="iexact", message=lite_content.lite_api.teams.Teams.NOT_UNIQUE_NAME, )
        ],
        error_messages={"blank": lite_content.lite_api.teams.Teams.BLANK_NAME},
    )

    class Meta:
        model = Team
        fields = ("id", "name")
