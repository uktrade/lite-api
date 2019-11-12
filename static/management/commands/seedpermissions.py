from static.management.SeedCommand import SeedCommand, SeedCommandTest
from users.models import Permission, Role, GovUser

FILE = 'lite-content/lite-api/permissions.csv'


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedpermissions
    """
    help = 'Seeds permissions'
    success = 'Successfully seeded permissions'
    seed_command = 'seedpermissions'

    def operation(self, *args, **options):
        reader = self.read_csv(FILE)
        for row in reader:
            Permission.objects.get_or_create(id=row[0], name=row[1])


class SeedPermissionsTests(SeedCommandTest):
    def test_seed_org_users(self):
        self.seed_command(Command)
        self.assertTrue(Permission.objects.count() >= len(Command.read_csv(FILE)))
