from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from content_strings.strings import get_string
from teams.models import Team


class TeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=50,
        validators=[
            UniqueValidator(
                queryset=Team.objects.all(),
                lookup="iexact",
                message=get_string("teams.not_unique_name"),
            )
        ],
        error_messages={"blank": get_string("teams.blank_name")},
    )

    class Meta:
        model = Team
        fields = ("id", "name")
