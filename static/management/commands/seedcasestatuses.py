from static.management.SeedCommand import SeedCommand, SeedCommandTest
from static.statuses.models import CaseStatus, CaseStatusOnType

STATUSES_FILE = 'lite_content/lite-api/case_statuses.csv'
STATUS_ON_TYPE_FILE = 'lite_content/lite-api/case_status_on_type.csv'


class Command(SeedCommand):
    help = 'Creates case statuses and case statuses on case types.'
    success = 'Successfully seeded case statuses'
    seed_command = 'seedcasestatuses'

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedcasestatuses
        """
        reader = self.read_csv(STATUSES_FILE)
        for row in reader:
            CaseStatus.objects.get_or_create(status=row[0], priority=row[1], is_read_only=row[2])

        status_ids = {status.status: status for status in CaseStatus.objects.all()}

        # Case statuses on case types
        for row in self.read_csv(STATUS_ON_TYPE_FILE):
            CaseStatusOnType.objects.get_or_create(type=row[0], status=status_ids[row[1]])


class SeedCaseStatusesTests(SeedCommandTest):
    def test_seed_case_statuses(self):
        self.seed_command(Command)
        self.assertTrue(CaseStatus.objects.count() == len(self.read_csv(STATUSES_FILE)))
