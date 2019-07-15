from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator

from content_strings.strings import get_string
from gov_users.enums import GovUserStatuses
from gov_users.models import GovUser, Role, Permission
from teams.models import Team


class GovUserSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedField(queryset=Team.objects.all(),
                                  error_messages={
                                      'null': get_string('users.null_team'),
                                  })
    status = serializers.ChoiceField(choices=GovUserStatuses.choices, default=GovUserStatuses.ACTIVE)
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=GovUser.objects.all())],
        error_messages={
            'blank': get_string('users.invalid_email'),
            'invalid': get_string('users.invalid_email'),
        }
    )
    team_name = serializers.SerializerMethodField()
    role = PrimaryKeyRelatedField(queryset=Role.objects.all())

    def get_team_name(self, instance):
        return instance.team.name

    class Meta:
        model = GovUser
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'status',
                  'role',
                  'team',
                  'team_name')

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.team = validated_data.get('team', instance.team)
        instance.role = validated_data.get('role', instance.role)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance


class GovUserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovUser
        fields = ('id',
                  'first_name',
                  'last_name',
                  'email')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id',
                  'name')


class RoleSerializer(serializers.ModelSerializer):
    permissions = PrimaryKeyRelatedField(queryset=Permission.objects.all(), many=True, )

    class Meta:
        model = Role
        fields = ('id',
                  'name',
                  'permissions')
