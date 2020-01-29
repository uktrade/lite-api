from django.db import transaction

from static.countries.models import Country
from static.management.SeedCommand import SeedCommand

COUNTRIES_FILE = "lite_content/lite_api/countries.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcountries
    """

    help = "Seeds all countries"
    info = "Seeding countries"
    success = "Successfully seeded countries"
    seed_command = "seedcountries"

    @transaction.atomic
    def operation(self, *args, **options):
        csv = self.read_csv(COUNTRIES_FILE)
        self.update_or_create(Country, csv)
        self.delete_unused_objects(Country, csv)
