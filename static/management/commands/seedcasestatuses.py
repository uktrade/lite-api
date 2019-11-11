from static.management.SeedCommand import SeedCommand
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus

class Command(SeedCommand):
    help = 'Creates case statuses'
    success = 'Successfully seeded case statuses'

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedcasestatuses
        """
        CaseStatus.objects.all().delete()

        for choice in CaseStatusEnum.choices:
            CaseStatus.objects.create(status=choice[0], priority=CaseStatusEnum.priority[choice[0]],
                                      is_read_only=CaseStatusEnum.is_read_only[choice[0]])
