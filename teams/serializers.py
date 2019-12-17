from lite_content.lite_api import teams

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from teams.models import Team


class TeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=50,
        validators=[
            UniqueValidator(
                queryset=Team.objects.all(), lookup="iexact", message=teams.Teams.NOT_UNIQUE_NAME,
            )
        ],
        error_messages={"blank": teams.Teams.BLANK_NAME},
    )

    class Meta:
        model = Team
        fields = ("id", "name")
