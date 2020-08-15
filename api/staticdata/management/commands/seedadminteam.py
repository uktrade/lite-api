from django.db import transaction

from api.conf.constants import Teams
from api.static.management.SeedCommand import SeedCommand
from api.teams.models import Team


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedadminteam
    """

    help = "Seeds the internal admin team"
    info = "Seeding admin team"
    seed_command = "seedadminteam"

    @transaction.atomic
    def operation(self, *args, **options):

        _, created = Team.objects.get_or_create(id=Teams.ADMIN_TEAM_ID, defaults={"name": Teams.ADMIN_TEAM_NAME})

        if created:
            self.print_created_or_updated(
                Team, dict(id=Teams.ADMIN_TEAM_ID, name=Teams.ADMIN_TEAM_NAME), is_created=True
            )
