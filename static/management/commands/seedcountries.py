from static.countries.models import Country
from static.management.SeedCommand import SeedCommand, SeedCommandTest


FILE = "lite_content/lite-api/countries.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcountries
    """

    help = "Seeds all countries"
    success = "Successfully seeded countries"
    seed_command = "seedcountries"

    def operation(self, *args, **options):
        csv = self.read_csv(FILE)
        self.update_or_create(Country, csv)


class SeedCountriesTests(SeedCommandTest):
    def test_seed_countries(self):
        self.seed_command(Command)
        self.assertTrue(Country.objects.count() == len(Command.read_csv(FILE)))
