import json

from conf.settings import env
from static.management.SeedCommand import SeedCommand, SeedCommandTest
from teams.models import Team
from users.models import GovUser, Role, Permission


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedgovuser
    """
    help = 'Seeds gov user'
    success = 'Successfully seeded gov user'
    seed_command = 'seedgovuser'

    def operation(self, *args, **options):
        Team.objects.get_or_create(id='00000000-0000-0000-0000-000000000001', name='Admin')
        Role.objects.get_or_create(id='00000000-0000-0000-0000-000000000001', name='Default')
        for email in json.loads(env('SEED_USERS')):
            GovUser.objects.get_or_create(email=email, team=Team.objects.get())


class SeedGovUserTests(SeedCommandTest):
    def test_seed_gov_user(self):
        self.seed_command(Command)
        self.assertTrue(Permission.objects)
        self.assertTrue(GovUser.objects)
        self.assertTrue(Role.objects)
