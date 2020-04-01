from django.db import transaction

from addresses.models import Address
from organisations.enums import OrganisationStatus, OrganisationType
from organisations.models import Organisation, Site
from organisations.tests.factories import OrganisationFactory, SiteFactory
from organisations.tests.providers import OrganisationProvider
from static.countries.helpers import get_country
from static.management.SeedCommand import SeedCommand

from faker import Faker

faker = Faker()
faker.add_provider(OrganisationProvider)

# To seed more organisations, add them to the lists below
COMMERCIAL_ORGANISATIONS = [
    {"name": "Archway Communications", "type": OrganisationType.COMMERCIAL, "reg_no": "09876543"},
]
HMRC_ORGANISATIONS = [
    {"name": "HMRC office at Battersea heliport", "type": OrganisationType.HMRC, "reg_no": "75863840"},
]


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedorganisations
    """

    help = "Seeds organisations"
    info = "Seeding exporter organisations"
    success = "Successfully seeded organisations"
    seed_command = "seedorganisations"

    @transaction.atomic
    def operation(self, *args, **options):
        org_name = options.get("organisation")
        sites = options.get("sites")

        if org_name or sites:
            self.seed_organisation(org_name, sites)
        else:
            self.seed_default_organisations()

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument("--organisation", help="Name of organisation to add", type=str)
        parser.add_argument("--sites", help="Number of sites to add", type=int)

    @classmethod
    def seed_default_organisations(cls):
        for organisation in COMMERCIAL_ORGANISATIONS + HMRC_ORGANISATIONS:
            org, org_created = Organisation.objects.get_or_create(
                name=organisation["name"],
                type=organisation["type"],
                eori_number="1234567890AAA",
                sic_number="2345",
                vat_number="GB1234567",
                registration_number=organisation["reg_no"],
                status=OrganisationStatus.ACTIVE,
            )

            address, address_created = Address.objects.get_or_create(
                address_line_1="42 Question Road",
                address_line_2="",
                country=get_country("GB"),
                city="London",
                region="London",
                postcode="Islington",
            )

            site, site_created = Site.objects.get_or_create(name="Headquarters", organisation=org, address=address)

            created = org_created and address_created and site_created

            if created or org.primary_site != site:
                org.primary_site = site
                org.save()
                data = dict(name=org.name, type=org.type, primary_site=site.name)
                cls.print_created_or_updated(Organisation, data, is_created=created)

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
