from django.db import transaction

from addresses.models import Address
from organisations.enums import OrganisationStatus, OrganisationType
from organisations.models import Organisation, Site
from static.countries.helpers import get_country
from static.management.SeedCommand import SeedCommand

DEFAULT_DEMO_ORG_NAME = "Archway Communications"
DEFAULT_DEMO_HMRC_ORG_NAME = "HMRC office at Battersea heliport"

# To seed more organisations, add them to the lists below
COMMERCIAL_ORGANISATIONS = [
    {"name": DEFAULT_DEMO_ORG_NAME, "type": OrganisationType.COMMERCIAL, "reg_no": "09876543"},
]

HMRC_ORGANISATIONS = [
    {"name": DEFAULT_DEMO_HMRC_ORG_NAME, "type": OrganisationType.HMRC, "reg_no": "75863840"},
]


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedorganisations
    """

    help = "Seeds organisations to demo with"
    info = "Seeding exporter organisations to demo with"
    success = "Successfully seeded organisations"
    seed_command = "seedorganisations"

    def handle(self, *args, **options):
        super().handle(*args, **options)

    @transaction.atomic
    def operation(self, *args, **options):
        self.seed_default_organisations()

    @classmethod
    def seed_default_organisations(cls):
        for organisation in COMMERCIAL_ORGANISATIONS + HMRC_ORGANISATIONS:
            org, _ = Organisation.objects.get_or_create(
                name=organisation["name"],
                type=organisation["type"],
                eori_number="1234567890AAA",
                sic_number="2345",
                vat_number="GB1234567",
                registration_number=organisation["reg_no"],
                status=OrganisationStatus.ACTIVE,
            )

            address, _ = Address.objects.get_or_create(
                address_line_1="42 Question Road",
                address_line_2="",
                country=get_country("GB"),
                city="London",
                region="London",
                postcode="Islington",
            )

            site, _ = Site.objects.get_or_create(name="Headquarters", organisation=org, address=address)
            org.primary_site = site
            org.save()
