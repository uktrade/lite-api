from django.db import transaction

from applications.enums import F680ClearanceTypeEnum
from applications.models import F680ClearanceType
from conf import settings

from static.management.SeedCommand import SeedCommand


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedf680clearancetypes
    """
    help = "Creates F680 clearance types"
    info = "Seeding F680 clearance types"
    success = "Successfully seeded F680 clearance types"
    seed_command = "seedf680clearancetypes"

    @transaction.atomic
    def operation(self, *args, **options):

        for f680_clearance_type in F680ClearanceTypeEnum.choices:
            _, created = F680ClearanceType.objects.update_or_create(
                id=F680ClearanceTypeEnum.ids[f680_clearance_type[0]], defaults={"name": [f680_clearance_type[0]]}
            )
            if not settings.SUPPRESS_TEST_OUTPUT:
                if created:
                    print(f"CREATED F680ClearanceType: {{'name': {f680_clearance_type[1]}}}")
                else:
                    print(f"UPDATED F680ClearanceType: {{'name': {f680_clearance_type[1]}}}")
