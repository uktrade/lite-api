from flags.models import Flag
from static.management.SeedCommand import SeedCommand
from teams.models import Team

SYSTEM_FLAGS_FILE = "lite_content/lite-api/system_flags.csv"

DEFAULT_ID = "00000000-0000-0000-0000-000000000001"
TEAM_NAME = "Admin"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedsystemflags
    """

    help = "Creates system flags"
    info = "Seeding system flags..."
    success = "Successfully seeded system flags"
    seed_command = "seedsystemflags"

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedsystemflags
        """
        Team.objects.get_or_create(id=DEFAULT_ID, name=TEAM_NAME)
        csv = self.read_csv(SYSTEM_FLAGS_FILE)
        self.update_or_create(Flag, csv)
        self.delete_unused_objects(Flag, csv)
