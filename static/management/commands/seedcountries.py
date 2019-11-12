import csv

from static.countries.models import Country
from static.management.SeedCommand import SeedCommand, SeedCommandTest


FILE = 'lite-content/lite-api/countries.csv'

class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcountries
    """
    help = 'Seeds all countries'
    success = 'Successfully seeded countries'
    seed_command = 'seedcountries'

    def operation(self, *args, **options):
        reader = self.read_csv(FILE)
        for row in reader:
            Country.objects.get_or_create(id=row[1], name=row[0], type=row[2])


class SeedCountriesTests(SeedCommandTest):
    def test_seed_countries(self):
        self.seed_command(Command)
        self.assertTrue(Country.objects.count() == len(Command.read_csv(FILE)))
