from django.db import transaction

from api.flags.models import Flag
from static.management.SeedCommand import SeedCommand

FLAGS_FILE = "lite_content/lite_api/system_flags.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedflags
    """

    help = "Seeds flags"
    info = "Seeding flags"
    seed_command = "seedflags"

    @transaction.atomic
    def operation(self, *args, **options):
        csv = self.read_csv(FLAGS_FILE)
        self.update_or_create(Flag, csv)
