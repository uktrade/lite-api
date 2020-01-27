import json

from django.db import transaction

from conf.settings import env
from static.management.SeedCommand import SeedCommand
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
        assert Role.objects.count(), "Role permissions must be seeded first!"

        super_user_role = Role.objects.get(id=SUPER_USER_ROLE_ID)
        # Default team
        team = Team.objects.get_or_create(id=DEFAULT_ID, name=TEAM_NAME)[0]

        # "Default" role
        Role.objects.get_or_create(id=DEFAULT_ID, name=ROLE_NAME)

        # "Super User" role
        super_user = Role.objects.get_or_create(id=SUPER_USER_ROLE_ID, name=SUPER_USER_ROLE_NAME)[0]

        # Add all permissions to the super user role
        super_user.permissions.set(Permission.internal.all())
        super_user.save()

        # Create all SEED_USERS and give them the super user role
        for email in json.loads(env("SEED_USERS")):
            gov_user_data = dict(email=email, team=team, role=super_user_role)
            _, created = GovUser.objects.get_or_create(email__iexact=email, defaults=gov_user_data)
            if created:
                print(f"CREATED GovUser: {gov_user_data}")
