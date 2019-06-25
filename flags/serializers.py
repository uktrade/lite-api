from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator

from content_strings.strings import get_string
from flags.enums import FlagLevels, FlagStatuses
from flags.models import Flag
from teams.models import Team


class FlagSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedField(queryset=Team.objects.all())
    level = serializers.ChoiceField(choices=FlagLevels.choices,
                                    error_messages={'invalid_choice': get_string('flags.error_messages.blank_level')})
    status = serializers.ChoiceField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE)
    name = serializers.CharField(
        max_length=20,
        validators=[UniqueValidator(queryset=Flag.objects.all(), lookup='iexact',
                                    message=get_string('flags.error_messages.non_unique'))],
        error_messages={'blank': get_string('flags.error_messages.blank_name')})

    team_name = serializers.SerializerMethodField()

    def get_team_name(self, instance):
        return instance.team.name

    class Meta:
        model = Flag
        fields = ('id',
                  'name',
                  'level',
                  'team',
                  'status',
                  'team_name')

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.name = validated_data.get('name', instance.name)
        instance.level = validated_data.get('level', instance.level)
        instance.save()
        return instance
