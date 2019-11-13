import json

from conf.settings import env
from static.management.SeedCommand import SeedCommand, SeedCommandTest
from teams.models import Team
from users.models import GovUser, Role, Permission

DEFAULT_ID = '00000000-0000-0000-0000-000000000001'
TEAM_NAME = 'Admin'
ROLE_NAME = 'Default'


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedgovuser
    """
    help = 'Seeds gov user'
    success = 'Successfully seeded gov user'
    seed_command = 'seedgovuser'

    def operation(self, *args, **options):
        team = Team.objects.get_or_create(id=DEFAULT_ID, name=TEAM_NAME)[0]
        Role.objects.get_or_create(id=DEFAULT_ID, name=ROLE_NAME)
        for email in json.loads(env('SEED_USERS')):
            GovUser.objects.get_or_create(email=email, team=team)


class SeedGovUserTests(SeedCommandTest):
    def test_seed_gov_user(self):
        self.seed_command(Command)
        self.assertTrue(Permission.objects)
        self.assertTrue(GovUser.objects)
        self.assertTrue(Role.objects)
