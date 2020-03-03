from django.db import transaction

from conf.constants import Teams
from static.management.SeedCommand import SeedCommand
from teams.models import Team


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedteams
    """

    help = "Creates teams"
    info = "Seeding teams"
    success = "Successfully seeded teams"
    seed_command = "seedteams"

    @transaction.atomic
    def operation(self, *args, **options):
        _, created = Team.objects.get_or_create(id=Teams.ADMIN_TEAM_ID, defaults={"name": Teams.ADMIN_TEAM_NAME})

        if created:
            self.print_created_or_updated(
                Team, dict(id=Teams.ADMIN_TEAM_ID, name=Teams.ADMIN_TEAM_NAME), is_created=True
            )
