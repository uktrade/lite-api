from django.core.management import BaseCommand
from django.db import transaction

from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus

success_message = 'Case statuses seeded successfully!'


class Command(BaseCommand):
    help = 'Creates case statuses'

    @transaction.atomic
    def handle(self, *args, **options):
        """
        pipenv run ./manage.py seedcasestatuses
        """
        CaseStatus.objects.all().delete()

        for choice in CaseStatusEnum.choices:
            CaseStatus.objects.create(status=choice[0], priority=CaseStatusEnum.priority[choice[0]],
                                      is_read_only=CaseStatusEnum.is_read_only[choice[0]])

        self.stdout.write(self.style.SUCCESS(success_message))
