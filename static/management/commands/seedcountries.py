import csv

from static.countries.models import Country
from static.management.SeedCommand import SeedCommand


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcountries
    """
    help = 'Seeds all countries'
    success = 'Successfully seeded countries'

    def operation(self, *args, **options):
        Country.objects.all().delete()
        with open('lite-content/lite-api/countries.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            next(reader, None)  # skip the headers
            for row in reader:
                Country.objects.create(id=row[1], name=row[0], type=row[2])
                print("Seeded %s " % row[0])
