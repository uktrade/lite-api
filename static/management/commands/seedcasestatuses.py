from static.management.SeedCommand import SeedCommand, SeedCommandTest
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus

FILE = 'lite_content/lite-api/case_statuses.csv'


class Command(SeedCommand):
    help = 'Creates case statuses'
    success = 'Successfully seeded case statuses'
    seed_command = 'seedcasestatuses'

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedcasestatuses
        """
        reader = self.read_csv(FILE)
        for row in reader:
            CaseStatus.objects.get_or_create(status=row[0], priority=row[1], is_read_only=row[2])


class SeedCaseStatusesTests(SeedCommandTest):
    def test_seed_case_statuses(self):
        self.seed_command(Command)
        self.assertTrue(CaseStatus.objects.count() == len(self.read_csv(FILE)))
