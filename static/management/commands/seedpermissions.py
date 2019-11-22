from django.db import transaction

from static.management.SeedCommand import SeedCommand, SeedCommandTest
from users.models import Permission

PERMISSIONS_FILE = "lite_content/lite-api/permissions.csv"


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
        csv = self.read_csv(PERMISSIONS_FILE)
        self.update_or_create(Permission, csv)
        self.delete_unused_objects(Permission, csv)


class SeedPermissionsTests(SeedCommandTest):
    def test_seed_org_users(self):
        self.seed_command(Command)
        self.assertTrue(Permission.objects.count() >= len(Command.read_csv(PERMISSIONS_FILE)))
