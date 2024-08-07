from django.db import transaction, IntegrityError

from django.conf import settings
from api.staticdata.countries.models import Country
from api.staticdata.management.SeedCommand import SeedCommand

COUNTRIES_FILE = "lite_content/lite_api/countries.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcountries
    This seed command is different because ".objects" is the incorrect object manager for all countries
    """

    help = "Seeds countries"
    info = "Seeding countries"
    seed_command = "seedcountries"

    @transaction.atomic
    def operation(self, *args, **options):
        csv = self.read_csv(COUNTRIES_FILE)
        for row in csv:
            obj_id = row["id"]
            obj = Country.objects.filter(id=obj_id)
            if not obj.exists():
                Country.objects.create(**row)
                if not settings.SUPPRESS_TEST_OUTPUT:
                    print(f"CREATED {Country.__name__}: {dict(row)}")
            else:
                SeedCommand.update_if_not_equal(obj, row, exclude=["is_terminal", "is_read_only"])

        ids = [row["id"] for row in csv]
        for obj in Country.objects.all():
            id = str(obj.id)
            if id not in ids:
                try:
                    obj.delete()
                    if not settings.SUPPRESS_TEST_OUTPUT:
                        print(f"Unused object deleted {id} from {Country.__name__}")
                except IntegrityError:
                    if not settings.SUPPRESS_TEST_OUTPUT:
                        print(f"Object {id} could not be deleted due to foreign key constraint")
