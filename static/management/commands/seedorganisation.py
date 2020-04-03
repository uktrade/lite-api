from django.db import transaction

from conf.constants import Roles
from organisations.enums import OrganisationType
from organisations.models import Organisation
from organisations.tests.factories import OrganisationFactory, SiteFactory
from organisations.tests.providers import OrganisationProvider
from static.management.SeedCommand import SeedCommand

from faker import Faker

from test_helpers.helpers import create_exporter_users
from users.models import ExporterUser

faker = Faker()
faker.add_provider(OrganisationProvider)


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedorganisation
    """

    help = "Seeds an organisation with a number of sites and users"
    info = "Seeding organisation"
    success = "Successfully seeded organisation"
    seed_command = "seedorganisation"

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument("--name", help="Name of organisation to seed", type=str)
        parser.add_argument("--type", help=f"Type of organisation to seed: {str(OrganisationType.as_list())}", type=str)
        parser.add_argument("--sites", help="Total number of sites to seed", type=int)
        parser.add_argument("--users", help="Total number of users to seed", type=int)
        parser.add_argument(
            "--super-user", help="Email of an ExporterUser to set as a Super User on the Organisation", type=str
        )

    @transaction.atomic
    def operation(self, *args, **options):
        org_name = options.get("name") or faker.company()
        org_type = options.get("type") or OrganisationType.COMMERCIAL
        no_of_sites = options.get("sites") or 1
        no_of_users = options.get("users") or 1
        super_user = options.get("super_user")

        self.seed_organisation(org_name, org_type, no_of_sites, no_of_users, super_user)

    @classmethod
    def seed_organisation(cls, org_name, org_type, no_of_sites, no_of_users, super_user):
        if Organisation.objects.filter(name__iexact=org_name).exists():
            raise Exception(f"An Organisation with name: '{org_name}' already exists")

        organisation = OrganisationFactory(name=org_name, type=org_type)

        # Set the Organisation's Exporter Super User or create one
        super_user = (
            cls._get_exporter_super_user(super_user)
            if super_user
            else create_exporter_users(organisation, 1, role_id=Roles.EXPORTER_SUPER_USER_ROLE_ID)
        )

        exporter_users = [super_user]
        # Since a Super User has already been created and/or set, subtract 1 from total number of users to seed
        exporter_users += create_exporter_users(organisation, no_of_users - 1)

        sites = [organisation.primary_site]
        # Since OrganisationFactory has already created a Site, subtract 1 from total number of sites to seed
        sites += [SiteFactory(organisation=organisation) for _ in range(no_of_sites - 1)]

        cls._print_organisation_to_console(organisation, super_user)
        return [("organisation", organisation), ("sites", sites), ("exporter_users", exporter_users)]

    @classmethod
    def _get_exporter_super_user(cls, super_user):
        try:
            return ExporterUser.objects.get(email__exact=super_user)
        except ExporterUser.DoesNotExist:
            raise Exception(f"An ExporterUser with email '{super_user}' does not exist")

    @classmethod
    def _print_organisation_to_console(cls, organisation, org_super_user):
        organisation_representation = dict(
            id=str(organisation.id),
            primary_site_id=str(organisation.primary_site.id),
            super_user_id=str(org_super_user.id),
        )
        cls.print_created_or_updated(Organisation, organisation_representation, is_created=True)
