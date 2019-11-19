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
        statuses = {}
        for row in self.read_csv(STATUSES_FILE):
            status = CaseStatus.objects.get_or_create(status=row[1], priority=row[2], is_read_only=row[3])[0]
            statuses[row[0]] = status

        # Case statuses on case types
        for row in self.read_csv(STATUS_ON_TYPE_FILE):
            CaseStatusCaseType.objects.get_or_create(type=row[1], status=statuses[row[2]])


class SeedCaseStatusesTests(SeedCommandTest):
    def test_seed_case_statuses(self):
        self.seed_command(Command)
        self.assertTrue(CaseStatus.objects.count() == len(Command.read_csv(STATUSES_FILE)))
        self.assertTrue(CaseStatusCaseType.objects.count() == len(Command.read_csv(STATUS_ON_TYPE_FILE)))
