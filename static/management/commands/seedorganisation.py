from django.db import transaction

from organisations.models import Organisation, Site
from organisations.tests.factories import OrganisationFactory, SiteFactory
from organisations.tests.providers import OrganisationProvider
from static.management.SeedCommand import SeedCommand

from faker import Faker

faker = Faker()
faker.add_provider(OrganisationProvider)


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedorganisations
    """

    help = "Seeds and organisation with a number of sites"
    info = "Seeding organisation"
    success = "Successfully seeded organisation"
    seed_command = "seedorganisations"

    @transaction.atomic
    def operation(self, *args, **options):
        org_name = options.get("organisation")
        sites = options.get("sites")

        self.seed_organisation(org_name, sites)

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument("--organisation", help="Name of organisation to add", type=str)
        parser.add_argument("--sites", help="Number of sites to add", type=int)

    @classmethod
    def seed_organisation(cls, org_name=None, sites=1):
        org_name = org_name or faker.company()
        if not Organisation.objects.filter(name__iexact=org_name).exists():
            organisation = OrganisationFactory(name=org_name)

            data = dict(name=organisation.name, type=organisation.type, primary_site=organisation.primary_site.name)
            cls.print_created_or_updated(Organisation, data, is_created=True)

            # OrganisationFactory creates a primary_site, so seed 1 less site
            for _ in range(sites - 1):
                site = SiteFactory(organisation=organisation)
                data = dict(
                    name=site.name,
                    address=dict(
                        address_line_1=site.address.address_line_1, city=site.address.city, region=site.address.region
                    ),
                )
                cls.print_created_or_updated(Site, data, is_created=True)
