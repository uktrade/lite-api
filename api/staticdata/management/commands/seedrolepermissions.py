from django.db import transaction

from api.core.constants import GovPermissions, ExporterPermissions, Roles
from api.staticdata.management.SeedCommand import SeedCommand
from api.staticdata.statuses.models import CaseStatus
from api.users.enums import UserType
from api.users.models import Permission, Role


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedrolepermissions
    """

    help = "Seeds roles and permissions"
    info = "Seeding roles and permissions"
    seed_command = "seedrolepermissions"

    @transaction.atomic
    def operation(self, *args, **options):
        self.get_or_create_permission(GovPermissions, UserType.INTERNAL.value)
        self.get_or_create_permission(ExporterPermissions, UserType.EXPORTER.value)

        self.delete_unused_objects(
            Permission, [{"id": x.name} for x in GovPermissions] + [{"id": x.name} for x in ExporterPermissions]
        )

        self._create_role_and_output(
            id=Roles.INTERNAL_DEFAULT_ROLE_ID, type=UserType.INTERNAL.value, name=Roles.INTERNAL_DEFAULT_ROLE_NAME
        )
        self._create_role_and_output(
            id=Roles.EXPORTER_DEFAULT_ROLE_ID, type=UserType.EXPORTER.value, name=Roles.EXPORTER_DEFAULT_ROLE_NAME
        )
        self._create_role_and_output(
            id=Roles.EXPORTER_AGENT_ROLE_ID, type=UserType.EXPORTER.value, name=Roles.EXPORTER_AGENT_ROLE_NAME
        )
        self._create_role_and_output(
            id=Roles.INTERNAL_SUPER_USER_ROLE_ID, type=UserType.INTERNAL.value, name=Roles.INTERNAL_SUPER_USER_ROLE_NAME
        )
        self._create_role_and_output(
            id=Roles.EXPORTER_SUPER_USER_ROLE_ID, type=UserType.EXPORTER.value, name=Roles.EXPORTER_SUPER_USER_ROLE_NAME
        )

        # Add all permissions and statuses to internal super user
        role = Role.objects.get(id=Roles.INTERNAL_SUPER_USER_ROLE_ID)

        permissions = list(Permission.internal.all())
        role.permissions.add(*permissions)

        statuses = list(CaseStatus.objects.all())
        role.statuses.add(*statuses)

        role.save()

        # Add all permissions to exporter super user
        role = Role.objects.get(id=Roles.EXPORTER_SUPER_USER_ROLE_ID)

        permissions = list(Permission.exporter.all())
        role.permissions.add(*permissions)

        role.save()

        # Add agent permissions to Agent
        role = Role.objects.get(id=Roles.EXPORTER_AGENT_ROLE_ID)

        permission = Permission.objects.get(id=ExporterPermissions.SUBMIT_LICENCE_APPLICATION.name)
        role.permissions.add(permission)

        role.save()

    @classmethod
    def get_or_create_permission(cls, permissions, user_type):
        for permission in permissions:
            data = dict(name=permission.value, type=user_type)
            permission, created = Permission.objects.get_or_create(id=permission.name, defaults=data)

            if created or permission.type != user_type:
                permission.type = user_type
                permission.save()
                cls.print_created_or_updated(Permission, data, is_created=created)

    @classmethod
    def _create_role_and_output(cls, id, type, name):
        data = dict(id=str(id), type=type, name=name)
        _, created = Role.objects.get_or_create(**data)

        if created:
            cls.print_created_or_updated(Role, data, is_created=True)
