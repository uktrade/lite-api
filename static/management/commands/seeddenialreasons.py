from static.denial_reasons.models import DenialReason
from static.management.SeedCommand import SeedCommand, SeedCommandTest

FILE = "lite_content/lite-api/denial_reasons.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seeddenialreasons
    """

    help = "Seeds all denial reasons"
    success = "Successfully seeded denial reasons"
    seed_command = "seeddenialreasons"

    def operation(self, *args, **options):
        csv = self.read_csv(FILE)
        self.update_or_create(DenialReason, csv)


class SeedDenialReasonsTests(SeedCommandTest):
    def test_seed_denial_reasons(self):
        self.seed_command(Command)
        self.assertTrue(DenialReason.objects.count() == len(Command.read_csv(FILE)))
