from django.db import transaction

from cases.models import CaseType
from static.management.SeedCommand import SeedCommand

CASE_TYPES_FILE = "lite_content/lite_api/case_types.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcasetypes
    """

    help = "Creates case types"
    info = "Seeding case types"
    success = "Successfully seeded case types"
    seed_command = "seedcasetypes"

    @transaction.atomic
    def operation(self, *args, **options):
        csv = self.read_csv(CASE_TYPES_FILE)
        self.update_or_create(CaseType, csv)
        self.delete_unused_objects(CaseType, csv)
