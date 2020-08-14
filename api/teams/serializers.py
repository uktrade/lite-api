from lite_content.lite_api import strings
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.teams.models import Team


class TeamReadOnlySerializer(serializers.Serializer):
    """
    More performant read_only team serializer
    """

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)


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
