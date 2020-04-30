from applications.models import StandardApplication
from organisations.models import Organisation
from static.management.SeedCommand import SeedCommand
from users.models import ExporterUser

class Command(SeedCommand):
    """
    pipenv run ./manage.py seeddata>
    """

    help = "Seeds stats"
    info = "Gathering stats"
    success = "Successfully gathered stats"
    seed_command = "seedstats"

    def operation(self, *args, **options):

        print(f"Organisations:{Organisation.objects.all().count()}"
              f"\nSIELs:{StandardApplication.objects.all().count()}"
              f"\nExport Users:{ExporterUser.objects.all().count()}")
