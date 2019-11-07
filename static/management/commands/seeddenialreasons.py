import csv

from conf.helpers import str_to_bool
from static.denial_reasons.models import DenialReason
from static.management.SeedCommand import SeedCommand


class Command(SeedCommand):
    """
    pipenv run ./manage.py seeddenialreasons
    """
    help = 'Seeds all denial reasons'
    success = 'Successfully seeded denial reasons'

    def operation(self, *args, **options):
        DenialReason.objects.all().delete()
        with open('lite-content/lite-api/denial_reasons.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            next(reader, None)  # skip the headers
            for row in reader:
                item_id = row[0]
                item_is_deprecated = str_to_bool(row[1])
                DenialReason.objects.create(id=item_id, deprecated=item_is_deprecated)
