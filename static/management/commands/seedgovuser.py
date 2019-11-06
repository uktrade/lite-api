import json

from conf.settings import env
from static.management.SeedCommand import SeedCommand
from teams.models import Team
from users.models import GovUser, Role, Permission


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcountries
    """
    help = 'Seeds gov user'
    success = 'Successfully seeded gov user'

    def operation(self, *args, **options):
        if not Role.objects.all():
            Role.objects.create(id='00000000-0000-0000-0000-000000000001', name='Default')

        if not GovUser.objects.all():
            for email in json.loads(env('SEED_USERS')):
                GovUser.objects.create(email=email, team=Team.objects.get())

        if not Permission.objects.all():
            Permission.objects.create(id='MAKE_FINAL_DECISIONS', name='Make final decisions')
