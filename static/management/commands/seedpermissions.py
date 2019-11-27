from django.db import transaction

from conf import constants
from static.management.SeedCommand import SeedCommand, SeedCommandTest
from users.models import Permission


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedpermissions
    """

    help = "Seeds permissions"
    info = "Seeding permissions"
    success = "Successfully seeded permissions"
    seed_command = "seedpermissions"

    @transaction.atomic
    def operation(self, *args, **options):
        for permission in constants.Permission:
            Permission.objects.update_or_create(id=permission.name, defaults={"name": permission.value})
            print(f"CREATED: {permission.name}")

        self.delete_unused_objects(Permission, [{"id": x.name} for x in constants.Permission])


class SeedPermissionsTests(SeedCommandTest):
    def test_seed_org_users(self):
        self.seed_command(Command)
        self.assertTrue(Permission.objects.count() >= len(constants.Permission))
