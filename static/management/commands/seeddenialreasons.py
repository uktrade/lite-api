from django.db import transaction

from static.denial_reasons.models import DenialReason
from static.management.SeedCommand import SeedCommand, SeedCommandTest

DENIAL_REASONS_FILE = "lite_content/lite_api/denial_reasons.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seeddenialreasons
    """

    help = "Seeds all denial reasons"
    info = "Seeding denial reasons"
    success = "Successfully seeded denial reasons"
    seed_command = "seeddenialreasons"

    @transaction.atomic
    def operation(self, *args, **options):
        csv = self.read_csv(DENIAL_REASONS_FILE)
        self.update_or_create(DenialReason, csv)
        self.delete_unused_objects(DenialReason, csv)


class SeedDenialReasonsTests(SeedCommandTest):
    def test_seed_denial_reasons(self):
        self.seed_command(Command)
        self.assertTrue(DenialReason.objects.count() == len(Command.read_csv(DENIAL_REASONS_FILE)))
