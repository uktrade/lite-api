from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from teams.models import Team


class TeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=50,
        validators=[UniqueValidator(queryset=Team.objects.all(), lookup='iexact',
                                    message='Enter a name which is not already in use by another team')],
        error_messages={'blank': 'Team name may not be blank'})

    class Meta:
        model = Team
        fields = ('id',
                  'name')

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance
