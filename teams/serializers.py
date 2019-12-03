from lite_content.lite_api import strings
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from teams.models import Team


class TeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=50,
        validators=[
            UniqueValidator(queryset=Team.objects.all(), lookup="iexact", message=strings.Teams.NOT_UNIQUE_NAME,)
        ],
        error_messages={"blank": strings.Teams.BLANK_NAME},
    )

    class Meta:
        model = Team
        fields = ("id", "name")
