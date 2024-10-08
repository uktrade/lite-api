from json import loads as serialize
from django.db import transaction

from api.core.constants import Teams, Roles
from api.conf.settings import env
from api.queues.constants import ALL_CASES_QUEUE_ID
from api.staticdata.management.SeedCommand import SeedCommand
from api.users.enums import UserType
from api.users.models import Role, GovUser, BaseUser


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedinternalusers
    """

    help = "Seeds internal users to the admin team"
    info = "Seeding internal users"
    seed_command = "seedinternalusers"

    @transaction.atomic
    def operation(self, *args, **options):
        admin_users = self._get_internal_users_list()

        for admin_user in admin_users:
            email = admin_user["email"]
            team_id = admin_user.get("team_id", Teams.ADMIN_TEAM_ID)
            default_queue = admin_user.get("default_queue", ALL_CASES_QUEUE_ID)

            role = Role.objects.get(
                name=admin_user.get("role", Roles.INTERNAL_SUPER_USER_ROLE_NAME), type=UserType.INTERNAL
            )
            base_user, _ = BaseUser.objects.get_or_create(
                email__iexact=email, defaults={"email": email}, type=UserType.INTERNAL
            )
            admin_user, created = GovUser.objects.get_or_create(
                baseuser_ptr=base_user,
                defaults={"team_id": team_id, "role": role, "default_queue": default_queue},
            )

            if created or admin_user.role != role:
                admin_user.role = role
                admin_user.save()

                admin_data = dict(email=email, team=admin_user.team.name, role=role.name)
                self.print_created_or_updated(GovUser, admin_data, is_created=created)

        if not GovUser.objects.count() >= 1:
            raise Exception("You must have at least one GovUser seeded")

    @classmethod
    def _get_internal_users_list(cls):
        admin_users = env("INTERNAL_USERS")
        # The JSON representation of the variable is different on environments, so it needs to be parsed first
        parsed_admin_users = admin_users.replace("=>", ":")

        try:
            serialized_admin_users = serialize(parsed_admin_users)
        except ValueError:
            raise ValueError(
                f"INTERNAL_USERS has incorrect format;"
                f'\nexpected format: [{{"email": "", "role": ""}}]'
                f"\nbut got: {admin_users}"
            )

        return serialized_admin_users
