from json import loads as serialize
from django.db import transaction

from conf.constants import Teams, Roles
from conf.settings import env
from static.management.SeedCommand import SeedCommand
from teams.models import Team
from users.enums import UserType
from users.models import Role, GovUser


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedadminusers
    """

    help = "Seeds a gov admin team users so that other users can be added"
    info = "Seeding admin users"
    success = "Successfully seeded admin users"
    seed_command = "seedadminusers"

    @transaction.atomic
    def operation(self, *args, **options):
        assert Role.objects.count(), "Role permissions must be seeded first!"

        self.seed_admin_team()
        self.seed_internal_users()

    @classmethod
    def seed_admin_team(cls):
        _, created = Team.objects.get_or_create(id=Teams.ADMIN_TEAM_ID, defaults={"name": Teams.ADMIN_TEAM_NAME})

        if created:
            cls.print_created_or_updated(
                Team, dict(id=Teams.ADMIN_TEAM_ID, name=Teams.ADMIN_TEAM_NAME), is_created=True
            )

    @classmethod
    def seed_internal_users(cls):
        admin_users = env("INTERNAL_ADMIN_USERS")
        admin_users = admin_users.replace("=>", ":")
        admin_users = serialize(admin_users)

        for user in admin_users:
            email = user.get("email")
            role = Role.objects.get(name=user.get("role", Roles.INTERNAL_SUPER_USER_ROLE_NAME), type=UserType.INTERNAL)

            _, created = GovUser.objects.get_or_create(
                email__iexact=email, defaults={"email": email, "team_id": Teams.ADMIN_TEAM_ID, "role": role},
            )

            if created:
                admin_data = dict(email=email, team=Teams.ADMIN_TEAM_NAME, role=role.name)
                cls.print_created_or_updated(GovUser, admin_data, is_created=True)
