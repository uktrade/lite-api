import json

from conf.constants import Permissions
from conf.settings import env
from static.management.SeedCommand import SeedCommand, SeedCommandTest
from teams.models import Team
from users.models import GovUser, Role, Permission

DEFAULT_ID = "00000000-0000-0000-0000-000000000001"
SUPER_USER_ROLE_ID = "00000000-0000-0000-0000-000000000002"
SUPER_USER_ROLE_NAME = "Super User"
TEAM_NAME = "Admin"
ROLE_NAME = "Default"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedgovuser
    """

    help = "Seeds gov user"
    success = "Successfully seeded gov user"
    seed_command = "seedgovuser"

    def operation(self, *args, **options):
        # Default team
        team = Team.objects.get_or_create(id=DEFAULT_ID, name=TEAM_NAME)[0]

        # "Default" role
        Role.objects.get_or_create(id=DEFAULT_ID, name=ROLE_NAME)

        # "Super User" role
        super_user = Role.objects.get_or_create(id=SUPER_USER_ROLE_ID, name=SUPER_USER_ROLE_NAME)[0]

        # Add all permissions to the super user role
        role = Role.objects.get(id=SUPER_USER_ROLE_ID)
        role.permissions.set(
            [
                Permissions.MANAGE_FINAL_ADVICE,
                Permissions.MANAGE_TEAM_ADVICE,
                Permissions.REVIEW_GOODS,
                Permissions.ADMINISTER_ROLES,
                Permissions.MANAGE_TEAM_CONFIRM_OWN_ADVICE,
            ]
        )
        role.save()

        # Create all SEED_USERS and give them the super user role
        for email in json.loads(env("SEED_USERS")):
            GovUser.objects.get_or_create(email=email, team=team, role=super_user)


class SeedGovUserTests(SeedCommandTest):
    def test_seed_gov_user(self):
        self.seed_command(Command)
        self.assertTrue(Permission.objects)
        self.assertTrue(GovUser.objects)
        self.assertTrue(Role.objects)
