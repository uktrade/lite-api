from static.management.SeedCommand import SeedCommand, SeedCommandTest
from static.statuses.models import CaseStatus, CaseStatusCaseType

STATUSES_FILE = "lite_content/lite-api/case_statuses.csv"
STATUS_ON_TYPE_FILE = "lite_content/lite-api/case_status_on_type.csv"


class Command(SeedCommand):
    help = "Creates case statuses and case statuses on case types."
    success = "Successfully seeded case statuses"
    seed_command = "seedcasestatuses"

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedcasestatuses
        """
        # Case statuses
        status_csv = self.read_csv(STATUSES_FILE)
        self.update_or_create(CaseStatus, status_csv)

        case_to_status_csv = self.read_csv(STATUS_ON_TYPE_FILE)
        for row in case_to_status_csv:
            row['status'] = CaseStatus.objects.get(id=row['status'])
        self.update_or_create(CaseStatusCaseType, case_to_status_csv)

        self.delete_unused_objects(CaseStatus, status_csv)
        self.delete_unused_objects(CaseStatusCaseType, case_to_status_csv)


class SeedCaseStatusesTests(SeedCommandTest):
    def test_seed_case_statuses(self):
        self.seed_command(Command)
        self.assertTrue(CaseStatus.objects.count() == len(Command.read_csv(STATUSES_FILE)))
        self.assertTrue(CaseStatusCaseType.objects.count() == len(Command.read_csv(STATUS_ON_TYPE_FILE)))
