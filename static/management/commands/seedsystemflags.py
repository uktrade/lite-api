import uuid

from django.core.management import BaseCommand
from django.db import transaction

from flags.models import Flag
from flags.enums import SystemFlags

success_message = 'System flags seeded successfully!'


class Command(BaseCommand):
    help = 'Creates system flags'

    @transaction.atomic
    def handle(self, *args, **options):
        """
        pipenv run ./manage.py seedsystemflags
        """

        for choice in SystemFlags.flags:
            if not Flag.objects.filter(id=SystemFlags.id[choice[0]],
                                       team=uuid.UUID('00000000-0000-0000-0000-000000000001')).count():
                if Flag.objects.filter(id=SystemFlags.id[choice[0]]).count():
                    Flag.objects.filter(id=SystemFlags.id[choice[0]]).delete()
                Flag.objects.create(id=SystemFlags.id[choice[0]],
                                    name=choice[1], level='Case', status='Active',
                                    team_id=uuid.UUID('00000000-0000-0000-0000-000000000001'))

        self.stdout.write(self.style.SUCCESS(success_message))
