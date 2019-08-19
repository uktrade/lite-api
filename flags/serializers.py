from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from conf.serializers import PrimaryKeyRelatedSerializerField
from content_strings.strings import get_string
from flags.enums import FlagLevels, FlagStatuses
from flags.models import Flag
from teams.models import Team
from teams.serializers import TeamSerializer


class FlagSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamSerializer)
    level = serializers.ChoiceField(choices=FlagLevels.choices,
                                    error_messages={'invalid_choice': get_string('flags.error_messages.blank_level')})
    status = serializers.ChoiceField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE)
    name = serializers.CharField(
        max_length=20,
        trim_whitespace=True,
        validators=[UniqueValidator(queryset=Flag.objects.all(), lookup='iexact',
                                    message=get_string('flags.error_messages.non_unique'))],
        error_messages={'blank': get_string('flags.error_messages.blank_name')})

    class Meta:
        model = Flag
        fields = ('id',
                  'name',
                  'level',
                  'team',
                  'status',)

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.name = validated_data.get('name', instance.name)
        instance.level = validated_data.get('level', instance.level)
        instance.save()
        return instance
