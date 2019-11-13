from static.management.SeedCommand import SeedCommand, SeedCommandTest
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus


class Command(SeedCommand):
    help = 'Creates case statuses'
    success = 'Successfully seeded case statuses'
    seed_command = 'seedcasestatuses'

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedcasestatuses
        """
        for choice in CaseStatusEnum.choices:
            CaseStatus.objects.get_or_create(status=choice[0], priority=CaseStatusEnum.priority[choice[0]],
                                             is_read_only=CaseStatusEnum.is_read_only[choice[0]])


class SeedCaseStatusesTests(SeedCommandTest):
    def test_seed_case_statuses(self):
        self.seed_command(Command)
        self.assertTrue(CaseStatus.objects.count() == len(CaseStatusEnum.choices))
