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
    part_of_ecju = serializers.BooleanField(read_only=True)


class TeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=50,
        validators=[
            UniqueValidator(queryset=Team.objects.all(), lookup="iexact", message=strings.Teams.NOT_UNIQUE_NAME,)
        ],
        error_messages={"blank": strings.Teams.BLANK_NAME},
    )
    part_of_ecju = serializers.BooleanField(
        error_messages={
            "null": "Select yes if the team is part of ECJU",
            "required": "Select yes if the team is part of ECJU",
        }
    )

    class Meta:
        model = Team
        fields = "__all__"

    def validate(self, attrs):
        validated_data = super().validate(attrs)

        if "part_of_ecju" not in validated_data:
            raise serializers.ValidationError({"part_of_ecju": "Select yes if the team is part of ECJU"})

        return validated_data
