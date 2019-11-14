import uuid

from cases.models import Case
from flags.models import Flag
from flags.enums import SystemFlags
from goods.models import Good
from organisations.models import Organisation
from static.countries.models import Country
from static.management.SeedCommand import SeedCommand

success_message = 'System flags seeded successfully!'


class Command(SeedCommand):
    help = 'Creates system flags'
    success = 'Successfully seeded system flags'
    seed_command = 'seedsystemflags'

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedsystemflags
        """

        for choice in SystemFlags.flags:
            flag_id = SystemFlags.id[choice[0]]
            if not Flag.objects.filter(id=flag_id,
                                       team=uuid.UUID('00000000-0000-0000-0000-000000000001')).count():
                if Flag.objects.filter(id=flag_id).count():
                    flag = Flag.objects.filter(id=flag_id).update(id=uuid.uuid4())
                    if flag.level == 'Case':
                        Case.objects.filter(flags__id=flag_id).update(flag.id)
                    elif flag.level == 'Organisation':
                        Organisation.objects.filter(flags__id=flag_id).update(flag.id)
                    elif flag.level == 'Good':
                        Good.objects.filter(flags__id=flag_id).update(flag.id)
                    elif flag.level == 'Destination':
                        Country.objects.filter(flags__id=flag_id).update(flag.id)
                Flag.objects.create(id=flag_id,
                                    name=choice[1], level='Case', status='Active',
                                    team_id=uuid.UUID('00000000-0000-0000-0000-000000000001'))

        self.stdout.write(self.style.SUCCESS(success_message))
