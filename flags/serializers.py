from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator

from flags.enums import FlagLevels, FlagStatuses
from flags.models import Flag
from teams.models import Team


class FlagSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedField(queryset=Team.objects.all())
    level = serializers.ChoiceField(choices=FlagLevels.choices)
    status = serializers.ChoiceField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE)
    name = serializers.CharField(
        max_length=20,
        validators=[UniqueValidator(queryset=Flag.objects.all(), lookup='iexact',
                                    message='Enter a name which is not already in use by another flag')],
        error_messages={'blank': 'Flag name may not be blank'})

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
        instance.save()
        return instance
