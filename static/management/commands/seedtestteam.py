from static.management.SeedCommand import SeedCommand
from teams.models import Team


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedtestteam
    """
    help = 'Seeds all test teams'
    success = 'Successfully seeded test team'

    def operation(self, *args, **options):
        if not Team.objects.all():
            Team.objects.create(id='00000000-0000-0000-0000-000000000001', name='Admin')
