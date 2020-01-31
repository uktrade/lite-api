from django.db import transaction

from cases.enums import CaseTypeEnum
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
        data = CaseTypeEnum.as_list()
        # Rename key to id and value to name
        for item in data:
            item["id"] = item.pop("key")
            item["name"] = item.pop("value")

        print(data)
        self.update_or_create(CaseType, data)
        self.delete_unused_objects(CaseType, data)
