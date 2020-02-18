from django.db import transaction

from cases.enums import CaseTypeEnum
from conf import settings
from static.management.SeedCommand import SeedCommand

from static.statuses.models import CaseStatus, CaseStatusCaseType

STATUSES_FILE = "lite_content/lite_api/case_statuses.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcasestatuses
    """

    help = "Creates case statuses and case statuses on case types"
    info = "Seeding case statuses"
    success = "Successfully seeded case statuses"
    seed_command = "seedcasestatuses"

    STATUSES_ON_CASE_TYPES = {
        "00000000-0000-0000-0000-000000000001": ["application", "hmrc", "goods", "eua"],
        "00000000-0000-0000-0000-000000000002": {"application"},
        "00000000-0000-0000-0000-000000000003": ["application", "hmrc", "goods", "eua"],
        "00000000-0000-0000-0000-000000000004": {"application"},
        "00000000-0000-0000-0000-000000000005": {"application"},
        "00000000-0000-0000-0000-000000000006": {"application"},
        "00000000-0000-0000-0000-000000000007": {"application"},
        "00000000-0000-0000-0000-000000000008": {"application"},
    }

    @transaction.atomic
    def operation(self, *args, **options):
        status_csv = self.read_csv(STATUSES_FILE)
        self.update_or_create(CaseStatus, status_csv)
        self.delete_unused_objects(CaseStatus, status_csv)

        case_type_list = CaseTypeEnum.case_type_list

        # Use enum from populated case_types to assign new case_to_status
        for case_type in case_type_list:

            for key, value in self.STATUSES_ON_CASE_TYPES.items():

                # IF: sub-type is present in a STATUSES_ON_CASE_TYPE
                # OR IF: type is present but sub-type is not in a STATUSES_ON_CASE_TYPE (handles HMRC-applications)
                if case_type.sub_type in value or (case_type.type in value and case_type.sub_type not in value):
                    case_to_status_data = dict(case_type_id=case_type.id, status_id=key)
                    case_status_case_type = CaseStatusCaseType.objects.filter(**case_to_status_data)

                    if not case_status_case_type.exists():
                        CaseStatusCaseType.objects.create(**case_to_status_data)
                        if not settings.SUPPRESS_TEST_OUTPUT:
                            print(f"CREATED {CaseStatusCaseType.__name__}: {case_to_status_data}")
