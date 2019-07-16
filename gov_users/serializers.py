from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator

from content_strings.strings import get_string
from gov_users.enums import GovUserStatuses
from gov_users.models import GovUser, Role, Permission
from teams.models import Team
from teams.serializers import TeamSerializer


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id',
                  'name')


class RoleSerializer(serializers.ModelSerializer):
    permissions = PrimaryKeyRelatedField(queryset=Permission.objects.all(), many=True)
    name = serializers.CharField(max_length=30,
                                 validators=[UniqueValidator(queryset=Role.objects.all(), lookup='iexact',
                                                             message=get_string('roles.duplicate_name'))],
                                 error_messages={'blank': get_string('roles.blank_name')})

    class Meta:
        model = Role
        fields = ('id',
                  'name',
                  'permissions')


class GovUserViewSerializer(serializers.ModelSerializer):
    team = TeamSerializer()
    role = RoleSerializer()

    class Meta:
        model = GovUser
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'status',
                  'team',
                  'role',)


class GovUserCreateSerializer(GovUserViewSerializer):
    status = serializers.ChoiceField(choices=GovUserStatuses.choices, default=GovUserStatuses.ACTIVE)
    email = serializers.EmailField(validators=[UniqueValidator(queryset=GovUser.objects.all())],
                                   error_messages={
                                       'blank': get_string('users.invalid_email'),
                                       'invalid': get_string('users.invalid_email'),
                                   })
    team = PrimaryKeyRelatedField(queryset=Team.objects.all(),
                                  error_messages={
                                      'null': get_string('users.null_team'),
                                      'invalid': get_string('users.null_team'),
                                  })
    role = PrimaryKeyRelatedField(queryset=Role.objects.all(),
                                  error_messages={
                                      'null': get_string('users.null_role'),
                                      'invalid': get_string('users.null_role'),
                                  })

    class Meta:
        model = GovUser
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'status',
                  'team',
                  'role',)


class GovUserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovUser
        fields = ('id',
                  'first_name',
                  'last_name',
                  'email')
