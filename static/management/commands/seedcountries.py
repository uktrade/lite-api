import csv

from static.countries.models import Country
from static.management.SeedCommand import SeedCommand, SeedCommandTest


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcountries
    """
    help = 'Seeds all countries'
    success = 'Successfully seeded countries'
    seed_command = 'seedcountries'

    def operation(self, *args, **options):
        with open('lite-content/lite-api/countries.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            next(reader)  # skip the headers
            for row in reader:
                Country.objects.get_or_create(id=row[1], name=row[0], type=row[2])


class SeedCountriesTests(SeedCommandTest):
    def test_seed_countries(self):
        self.seed_command(Command)
        self.assertTrue(Country.objects.count() > 250)
