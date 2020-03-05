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
    pipenv run ./manage.py seedinternaladminusers
    """

    help = "Seeds internal admin-team users so that other users can be added"
    info = "Seeding internal admin-team users"
    success = "Successfully seeded internal admin-team users"
    seed_command = "seedinternaladminusers"

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
        admin_users = cls._get_internal_users_list()

        for admin_user in admin_users:
            email = admin_user.get("email")
            role = Role.objects.get(
                name=admin_user.get("role", Roles.INTERNAL_SUPER_USER_ROLE_NAME), type=UserType.INTERNAL
            )

            admin_user, created = GovUser.objects.get_or_create(
                email__iexact=email, defaults={"email": email, "team_id": Teams.ADMIN_TEAM_ID, "role": role},
            )

            if created or admin_user.role != role:
                admin_user.role = role
                admin_user.save()

                admin_data = dict(email=email, team=Teams.ADMIN_TEAM_NAME, role=role.name)
                cls.print_created_or_updated(GovUser, admin_data, is_created=created)

    @classmethod
    def _get_internal_users_list(cls):
        admin_users = env("INTERNAL_ADMIN_TEAM_USERS")
        # The JSON representation of the variable is different on environments, so it needs to be parsed first
        parsed_admin_users = admin_users.replace("=>", ":")

        try:
            serialized_admin_users = serialize(parsed_admin_users)
        except ValueError:
            raise ValueError(
                f"INTERNAL_ADMIN_TEAM_USERS has incorrect format;"
                f"\nexpected format: [{{'email': '', 'role': ''}}]"
                f"\nbut got: {admin_users}"
            )

        return serialized_admin_users
