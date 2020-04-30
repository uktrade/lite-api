from applications.models import StandardApplication
from organisations.models import Organisation
from goods.models import Good
from applications.models import GoodOnApplication
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
              f"\nSIEL applications:{StandardApplication.objects.all().count()}"
              f"\nOrganisation Products:{Good.objects.all().count()}"
              f"\nProducts used in SEIL applications:{GoodOnApplication.objects.all().count()}"
              f"\nExport Users:{ExporterUser.objects.all().count()}")
