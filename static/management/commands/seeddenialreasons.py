import csv

from conf.helpers import str_to_bool
from static.denial_reasons.models import DenialReason
from static.management.SeedCommand import SeedCommand, SeedCommandTest


class Command(SeedCommand):
    """
    pipenv run ./manage.py seeddenialreasons
    """
    help = 'Seeds all denial reasons'
    success = 'Successfully seeded denial reasons'
    seed_command = 'seeddenialreasons'

    def operation(self, *args, **options):
        with open('lite-content/lite-api/denial_reasons.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            next(reader, None)  # skip the headers
            for row in reader:
                item_id = row[0]
                item_is_deprecated = str_to_bool(row[1])
                DenialReason.objects.get_or_create(id=item_id, deprecated=item_is_deprecated)


class SeedDenialReasonsTests(SeedCommandTest):
    def test_seed_denial_reasons(self):
        self.seed_command(Command)
        self.assertTrue(DenialReason.objects.count() > 25)
