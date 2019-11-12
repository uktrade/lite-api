from static.management.SeedCommand import SeedCommand, SeedCommandTest
from users.models import Permission, Role, GovUser

PERMISSIONS = {
    'MANAGE_TEAM_ADVICE': 'Manage team advice',
    'MANAGE_FINAL_ADVICE': 'Manage final advice'
}


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedpermissions
    """
    help = 'Seeds permissions'
    success = 'Successfully seeded permissions'
    seed_command = 'seedpermissions'

    def operation(self, *args, **options):
        for id, name in PERMISSIONS.items():
            Permission.objects.get_or_create(id=id, name=name)


class SeedPermissionsTests(SeedCommandTest):
    def test_seed_org_users(self):
        self.seed_command(Command)
        self.assertTrue(Permission.objects.count() == len(PERMISSIONS))
