from django.db import transaction

from api.static.management.SeedCommand import SeedCommand
from api.static.f680_clearance_types.enums import F680ClearanceTypeEnum
from api.static.f680_clearance_types.models import F680ClearanceType


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedf680clearancetypes
    """

    help = "Creates f680 clearance types"
    info = "Seeding f680 clearance types"
    seed_command = "seedf680clearancetypes"

    @transaction.atomic
    def operation(self, *args, **options):
        for type in F680ClearanceTypeEnum.choices:
            id = F680ClearanceTypeEnum.ids[type[0]]
            name = type[0]
            data = dict(id=id, name=name)

            f680_clearance_type, created = F680ClearanceType.objects.get_or_create(id=id, defaults=data)

            if created or f680_clearance_type.name != name:
                f680_clearance_type.name = name
                f680_clearance_type.save()
                self.print_created_or_updated(F680ClearanceType, data, is_created=created)
