from django.db import transaction

from static.management.SeedCommand import SeedCommand

from static.statuses.models import CaseStatus, CaseStatusCaseType

STATUSES_FILE = "lite_content/lite_api/case_statuses.csv"
STATUS_ON_TYPE_FILE = "lite_content/lite_api/case_status_on_type.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcasestatuses
    """

    help = "Creates case statuses and case statuses on case types"
    info = "Seeding case statuses"
    success = "Successfully seeded case statuses"
    seed_command = "seedcasestatuses"

    @transaction.atomic
    def operation(self, *args, **options):
        status_csv = self.read_csv(STATUSES_FILE)
        self.update_or_create(CaseStatus, status_csv)

        case_to_status_csv = self.read_csv(STATUS_ON_TYPE_FILE)
        self.update_or_create(CaseStatusCaseType, case_to_status_csv)

        self.delete_unused_objects(CaseStatus, status_csv)
        self.delete_unused_objects(CaseStatusCaseType, case_to_status_csv)
