from static.management.SeedCommand import SeedCommand
from users.models import Permission


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcountries
    """
    help = 'Seeds permissions'
    success = 'Successfully seeded permissions'

    def operation(self, *args, **options):
        if not Permission.objects.filter(id='MANAGE_TEAM_ADVICE'):
            Permission.objects.create(id='MANAGE_TEAM_ADVICE', name='Manage team advice')

        if not Permission.objects.filter(id='MANAGE_FINAL_ADVICE'):
            Permission.objects.create(id='MANAGE_FINAL_ADVICE', name='Manage final advice')
