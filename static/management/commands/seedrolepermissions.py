from django.db import transaction

from conf.constants import GovPermissions, ExporterPermissions
from static.management.SeedCommand import SeedCommand, SeedCommandTest
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
        print(f"CREATED: {role}")


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedpermissions
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
            if created:
                print(f"CREATED GOV PERMISSION: {permission.name}")
            else:
                print(f"UPDATED GOV PERMISSION: {permission.name}")

        for permission in ExporterPermissions:
            _, created = Permission.objects.update_or_create(
                id=permission.name, defaults={"name": permission.value, "type": UserType.EXPORTER}
            )
            if created:
                print(f"CREATED EXPORTER PERMISSION: {permission.name}")
            else:
                print(f"UPDATED EXPORTER PERMISSION: {permission.name}")

        self.delete_unused_objects(
            Permission, [{"id": x.name} for x in GovPermissions] + [{"id": x.name} for x in ExporterPermissions]
        )

        _create_role_and_output(id=DEFAULT_ID, type=UserType.INTERNAL, name=ROLE_NAME)
        _create_role_and_output(id=EX_DEFAULT_ID, type=UserType.EXPORTER, name=ROLE_NAME)
        _create_role_and_output(id=SUPER_USER_ROLE_ID, type=UserType.INTERNAL, name=SUPER_USER)
        _create_role_and_output(id=EX_SUPER_USER_ROLE_ID, type=UserType.EXPORTER, name=SUPER_USER)

        role = Role.objects.get(id=SUPER_USER_ROLE_ID)
        for permission in Permission.internal.all():
            role.permissions.add(permission)
        role.save()

        role = Role.objects.get(id=EX_SUPER_USER_ROLE_ID)
        for permission in Permission.exporter.all():
            role.permissions.add(permission)
        role.save()


class SeedPermissionsTests(SeedCommandTest):
    def test_seed_org_users(self):
        self.seed_command(Command)
        self.assertTrue(Permission.objects.count() >= len(GovPermissions) + len(ExporterPermissions))
