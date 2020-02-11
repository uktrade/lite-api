from django.db import transaction

from cases.enums import CaseTypeExtendedEnum
from cases.models import CaseType
from static.management.SeedCommand import SeedCommand


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
        extended_enums_list = CaseTypeExtendedEnum.extended_enums_list()
        data = []
        # Convert extended_enums_list from list of objects to list of dicts
        for extended_enum_obj in extended_enums_list:
            extended_enum_dict = dict(
                id=extended_enum_obj.id,
                reference=extended_enum_obj.reference,
                type=extended_enum_obj.type,
                sub_type=extended_enum_obj.sub_type,
            )
            data.append(extended_enum_dict)

        self.update_or_create(CaseType, data)
        self.delete_unused_objects(CaseType, data)
