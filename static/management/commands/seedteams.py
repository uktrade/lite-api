from django.db import transaction

from static.management.SeedCommand import SeedCommand
from teams.models import Team

ADMIN_TEAM_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_TEAM_NAME = "Admin"


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
        _, created = Team.objects.get_or_create(id=ADMIN_TEAM_ID, defaults={"name": ADMIN_TEAM_NAME})

        if created:
            self.print_created_or_updated(Team, dict(id=ADMIN_TEAM_ID, name=ADMIN_TEAM_NAME), is_created=True)
