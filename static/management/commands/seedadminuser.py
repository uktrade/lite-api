from django.db import transaction

from conf.constants import Teams, Roles
from conf.settings import env
from static.management.SeedCommand import SeedCommand
from teams.models import Team
from users.models import Role, GovUser


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedadminuser
    """

    help = "Seeds an initial gov super user so that other users can be added"
    info = "Seeding admin user"
    success = "Successfully seeded admin user"
    seed_command = "seedadminuser"

    @transaction.atomic
    def operation(self, *args, **options):
        assert Team.objects.count(), "Teams must be seeded first!"
        assert Role.objects.count(), "Role permissions must be seeded first!"

        admin_user = env("ADMIN_USER")

        _, created = GovUser.objects.get_or_create(
            email__iexact=admin_user,
            defaults={
                "email": admin_user,
                "team_id": Teams.ADMIN_TEAM_ID,
                "role_id": Roles.INTERNAL_SUPER_USER_ROLE_ID,
            },
        )

        if created:
            admin_data = dict(email=admin_user, team=Teams.ADMIN_TEAM_NAME, role=Roles.INTERNAL_SUPER_USER_ROLE_NAME)
            self.print_created_or_updated(GovUser, admin_data, is_created=True)
