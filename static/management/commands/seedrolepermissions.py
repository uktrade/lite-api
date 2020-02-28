from django.db import transaction

from conf.constants import GovPermissions, ExporterPermissions
from static.management.SeedCommand import SeedCommand
from static.statuses.models import CaseStatus
from users.enums import UserType
from users.models import Permission, Role

ROLE_GOV_DEFAULT_ID = "00000000-0000-0000-0000-000000000001"
ROLE_GOV_SUPER_USER_ID = "00000000-0000-0000-0000-000000000002"
ROLE_EXPORTER_SUPER_USER_ID = "00000000-0000-0000-0000-000000000003"
ROLE_EXPORTER_DEFAULT_ID = "00000000-0000-0000-0000-000000000004"
ROLE_DEFAULT_NAME = "Default"
ROLE_SUPER_USER_NAME = "Super User"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedrolepermissions
    """

    help = "Creates and updates default roles and permissions"
    info = "Seeding roles and permissions"
    success = "Successfully seeded roles and permissions"
    seed_command = "seedrolepermissions"

    @transaction.atomic
    def operation(self, *args, **options):
        self.get_or_update_permission(GovPermissions, UserType.INTERNAL)
        self.get_or_update_permission(ExporterPermissions, UserType.EXPORTER)

        self.delete_unused_objects(
            Permission, [{"id": x.name} for x in GovPermissions] + [{"id": x.name} for x in ExporterPermissions]
        )

        self._create_role_and_output(id=ROLE_GOV_DEFAULT_ID, type=UserType.INTERNAL, name=ROLE_DEFAULT_NAME)
        self._create_role_and_output(id=ROLE_EXPORTER_DEFAULT_ID, type=UserType.EXPORTER, name=ROLE_DEFAULT_NAME)
        self._create_role_and_output(id=ROLE_GOV_SUPER_USER_ID, type=UserType.INTERNAL, name=ROLE_SUPER_USER_NAME)
        self._create_role_and_output(id=ROLE_EXPORTER_SUPER_USER_ID, type=UserType.EXPORTER, name=ROLE_SUPER_USER_NAME)

        # Add all permissions and statuses to internal super user
        role = Role.objects.get(id=ROLE_GOV_SUPER_USER_ID)

        permissions = list(Permission.internal.all())
        role.permissions.add(*permissions)

        statuses = list(CaseStatus.objects.all())
        role.statuses.add(*statuses)

        role.save()

        # Add all permissions to exporter super user
        role = Role.objects.get(id=ROLE_EXPORTER_SUPER_USER_ID)

        permissions = list(Permission.exporter.all())
        role.permissions.add(*permissions)

        role.save()

    @classmethod
    def get_or_update_permission(cls, permissions, user_type):
        for permission in permissions:
            data = dict(name=permission.value, type=user_type)
            permission, created = Permission.objects.get_or_create(id=permission.name, defaults=data)

            if created or permission.type != user_type:
                permission.type = user_type
                permission.save()
                cls.print_created_or_updated(Permission, data, is_created=created)

    @classmethod
    def _create_role_and_output(cls, id, type, name):
        data = dict(id=id, type=type, name=name)
        _, created = Role.objects.get_or_create(**data)

        if created:
            cls.print_created_or_updated(Role, data, is_created=True)
