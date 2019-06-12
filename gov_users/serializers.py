from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator

from gov_users.enums import GovUserStatuses
from gov_users.models import GovUser
from teams.models import Team


class GovUserSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedField(queryset=Team.objects.all())
    status = serializers.ChoiceField(choices=GovUserStatuses.choices, default=GovUserStatuses.ACTIVE)
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=GovUser.objects.all())],
        error_messages={
            'invalid': 'Enter an email address in the correct format, like name@example.com'}
    )

    class Meta:
        model = GovUser
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'status',
                  'team')

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.team = validated_data.get('team', instance.team)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance
