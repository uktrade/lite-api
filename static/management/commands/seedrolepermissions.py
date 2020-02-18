from django.db import transaction

from conf import settings
from conf.constants import GovPermissions, ExporterPermissions
from static.management.SeedCommand import SeedCommand
from static.statuses.models import CaseStatus
from users.enums import UserType
from users.models import Permission, Role

DEFAULT_ID = "00000000-0000-0000-0000-000000000001"
SUPER_USER_ROLE_ID = "00000000-0000-0000-0000-000000000002"
EX_SUPER_USER_ROLE_ID = "00000000-0000-0000-0000-000000000003"
EX_DEFAULT_ID = "00000000-0000-0000-0000-000000000004"
TEAM_NAME = "Admin"
ROLE_NAME = "Default"
SUPER_USER = "Super User"


def _create_role_and_output(id, type, name):
    role, created = Role.objects.get_or_create(id=id, type=type, name=name)
    if created:
        role = dict(id=role.id, type=role.type, name=role.name)
        if not settings.SUPPRESS_TEST_OUTPUT:
            print(f"CREATED Role: {role}")


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

        for permission in GovPermissions:
            _, created = Permission.objects.update_or_create(
                id=permission.name, defaults={"name": permission.value, "type": UserType.INTERNAL}
            )
            if not settings.SUPPRESS_TEST_OUTPUT:
                if created:
                    print(f"CREATED Permission: {{'name': {permission.value}, 'type': {UserType.INTERNAL}}}")
                else:
                    print(f"UPDATED Permission: {{'name': {permission.value}, 'type': {UserType.INTERNAL}}}")

        for permission in ExporterPermissions:
            _, created = Permission.objects.update_or_create(
                id=permission.name, defaults={"name": permission.value, "type": UserType.EXPORTER}
            )
            if not settings.SUPPRESS_TEST_OUTPUT:
                if created:
                    print(f"CREATED Permission: {{'name': {permission.value}, 'type': {UserType.EXPORTER}}}")
                else:
                    print(f"UPDATED Permission: {{'name': {permission.value}, 'type': {UserType.EXPORTER}}}")

        self.delete_unused_objects(
            Permission, [{"id": x.name} for x in GovPermissions] + [{"id": x.name} for x in ExporterPermissions]
        )

        _create_role_and_output(id=DEFAULT_ID, type=UserType.INTERNAL, name=ROLE_NAME)
        _create_role_and_output(id=EX_DEFAULT_ID, type=UserType.EXPORTER, name=ROLE_NAME)
        _create_role_and_output(id=SUPER_USER_ROLE_ID, type=UserType.INTERNAL, name=SUPER_USER)
        _create_role_and_output(id=EX_SUPER_USER_ROLE_ID, type=UserType.EXPORTER, name=SUPER_USER)

        # Add all permissions and statuses to internal super user
        role = Role.objects.get(id=SUPER_USER_ROLE_ID)

        permissions = list(Permission.internal.all())
        role.permissions.add(*permissions)

        statuses = list(CaseStatus.objects.all())
        role.statuses.add(*statuses)

        role.save()

        # Add all permissions to exporter super user
        role = Role.objects.get(id=EX_SUPER_USER_ROLE_ID)

        permissions = list(Permission.exporter.all())
        role.permissions.add(*permissions)

        role.save()
