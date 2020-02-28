from django.db import transaction

from flags.models import Flag
from static.management.SeedCommand import SeedCommand
from teams.models import Team

FLAGS_FILE = "lite_content/lite_api/system_flags.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedflags
    """

    help = "Seeds flags"
    info = "Seeding flags"
    success = "Successfully seeded flags"
    seed_command = "seedflags"

    @transaction.atomic
    def operation(self, *args, **options):
        assert Team.objects.count(), "Teams must be seeded first!"

        csv = self.read_csv(FLAGS_FILE)
        self.update_or_create(Flag, csv)
