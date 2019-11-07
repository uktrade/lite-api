from static.management.SeedCommand import SeedCommand
from users.models import Permission


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcountries
    """
    help = 'Seeds permissions'
    success = 'Successfully seeded permissions'
    permissions = {
        'MANAGE_TEAM_ADVICE': 'Manage team advice',
        'MANAGE_FINAL_ADVICE': 'Manage final advice'
    }

    def operation(self, *args, **options):
        for id, name in self.permissions.items():
            if not Permission.objects.filter(id=id):
                Permission.objects.create(id=id, name=name)
