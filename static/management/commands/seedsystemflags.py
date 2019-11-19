from flags.models import Flag
from static.management.SeedCommand import SeedCommand
from teams.models import Team

FILE = "lite_content/lite-api/system_flags.csv"

DEFAULT_ID = "00000000-0000-0000-0000-000000000001"
TEAM_NAME = "Admin"


class Command(SeedCommand):
    help = "Creates system flags"
    success = "Successfully seeded system flags"
    seed_command = "seedsystemflags"

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedsystemflags
        """
        team = Team.objects.get_or_create(id=DEFAULT_ID, name=TEAM_NAME)[0]
        reader = self.read_csv(FILE)
        for row in reader:
            Flag.objects.get_or_create(
                id=row[0], name=row[1], level="Case", status="Deactivated", team_id=team.id,
            )
