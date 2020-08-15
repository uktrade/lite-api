from django.db import transaction

from cases.enums import CaseTypeEnum
from cases.models import CaseType
from api.static.management.SeedCommand import SeedCommand


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcasetypes
    """

    help = "Creates case types"
    info = "Seeding case types"
    seed_command = "seedcasetypes"

    @transaction.atomic
    def operation(self, *args, **options):
        case_type_list = CaseTypeEnum.CASE_TYPE_LIST
        data = []

        # Convert extended_enums_list from list of objects to list of dicts
        for case_type_obj in case_type_list:
            case_type_dict = dict(
                id=str(case_type_obj.id),
                reference=case_type_obj.reference,
                type=case_type_obj.type,
                sub_type=case_type_obj.sub_type,
            )
            data.append(case_type_dict)

        self.update_or_create(CaseType, data)
        self.delete_unused_objects(CaseType, data)
