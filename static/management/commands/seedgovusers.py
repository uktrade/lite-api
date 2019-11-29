import json

from django.db import transaction

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
    Must be run after `seedcountries`
    """

    help = "Seeds gov users"
    info = "Seeding gov users"
    success = "Successfully seeded gov users"
    seed_command = "seedgovusers"

    @transaction.atomic
    def operation(self, *args, **options):
        super_user_role = Role.objects.get(id=SUPER_USER_ROLE_ID)
        # Default team
        team = Team.objects.get_or_create(id=DEFAULT_ID, name=TEAM_NAME)[0]

        # "Default" role
        Role.objects.get_or_create(id=DEFAULT_ID, name=ROLE_NAME)

        # "Super User" role
        super_user = Role.objects.get_or_create(id=SUPER_USER_ROLE_ID, name=SUPER_USER_ROLE_NAME)[0]

        # Add all permissions to the super user role
        super_user.permissions.set(Permission.objects.all())
        super_user.save()

        # Create all SEED_USERS and give them the super user role
        for email in json.loads(env("SEED_USERS")):
            gov_user, created = GovUser.objects.get_or_create(email=email, team=team, role=super_user_role)
            if created:
                gov_user = dict(
                    email=gov_user.email,
                    first_name=gov_user.first_name,
                    last_name=gov_user.last_name,
                    role=gov_user.role.name,
                )
                print(f"CREATED: {gov_user}")


class SeedGovUserTests(SeedCommandTest):
    def test_seed_gov_user(self):
        self.seed_command(Command)
        self.assertTrue(Permission.objects)
        self.assertTrue(GovUser.objects)
        self.assertTrue(Role.objects)
