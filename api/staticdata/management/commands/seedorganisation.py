from django.db import transaction

from api.core.constants import Roles
from api.organisations.enums import OrganisationType
from api.organisations.models import Organisation
from api.organisations.tests.factories import OrganisationFactory, SiteFactory
from api.organisations.tests.providers import OrganisationProvider
from api.staticdata.management.SeedCommand import SeedCommand

from faker import Faker

from test_helpers.helpers import create_exporter_users
from api.users.models import ExporterUser, UserOrganisationRelationship

faker = Faker()
faker.add_provider(OrganisationProvider)


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedorganisation
    """

    help = "Seeds an organisation with a number of sites and users"
    info = "Seeding organisation"
    seed_command = "seedorganisation"

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument("--name", help="Name of Organisation to seed", type=str)
        parser.add_argument("--type", help=f"Type of Organisation to seed: {str(OrganisationType.as_list())}", type=str)
        parser.add_argument("--sites", help="Total number of Sites to seed", type=int)
        parser.add_argument("--users", help="Total number of Exporter Users to seed", type=int)
        parser.add_argument(
            "--primary-user", help="Email of an Exporter User to set as the Primary User of the Organisation", type=str
        )

    @transaction.atomic
    def operation(self, *args, **options):
        org_name = options.get("name") or faker.company()
        org_type = options.get("type") or OrganisationType.COMMERCIAL
        no_of_sites = options.get("sites") or 1
        no_of_users = options.get("users") or 1
        primary_user = options.get("primary_user")
        self.seed_organisation(org_name, org_type, no_of_sites, no_of_users, primary_user)

    @classmethod
    def seed_organisation(cls, org_name: str, org_type: str, no_of_sites: int, no_of_users: int, primary_user: str):
        if Organisation.objects.filter(name__iexact=org_name).exists():
            raise ValueError(f"An Organisation with name: '{org_name}' already exists")

        organisation = OrganisationFactory(name=org_name, type=org_type)

        # Sets a the Organisation's Primary Exporter User
        primary_user = cls._set_organisation_primary_user(organisation, primary_user)

        exporter_users = [primary_user]
        # Since a Primary User has already been created and/or set, subtract 1 from total number of users to seed
        exporter_users += create_exporter_users(organisation, no_of_users - 1)

        sites = [organisation.primary_site]
        # Since OrganisationFactory has already created a Site, subtract 1 from total number of sites to seed
        sites += [SiteFactory(organisation=organisation) for _ in range(no_of_sites - 1)]

        for site in sites:
            site.site_records_located_at = site
            site.save()

        cls._print_organisation_to_console(organisation, primary_user)
        return organisation, sites, exporter_users, primary_user

    @classmethod
    def _set_organisation_primary_user(cls, organisation: Organisation, primary_user: str):
        if not primary_user:
            return create_exporter_users(organisation, 1, role_id=Roles.EXPORTER_ADMINISTRATOR_ROLE_ID)[0]

        try:
            exporter_user = ExporterUser.objects.get(email__exact=primary_user)
        except ExporterUser.DoesNotExist:
            raise Exception(f"An Exporter User with email: '{primary_user}' does not exist")

        UserOrganisationRelationship.objects.create(
            organisation=organisation, user=exporter_user, role_id=Roles.EXPORTER_ADMINISTRATOR_ROLE_ID
        )

        return exporter_user

    @classmethod
    def _print_organisation_to_console(cls, organisation: Organisation, primary_user: ExporterUser):
        organisation_representation = dict(
            id=str(organisation.id),
            name=str(organisation.name),
            primary_site_id=str(organisation.primary_site.id),
            primary_user_id=str(primary_user.pk),
        )
        cls.print_created_or_updated(Organisation, organisation_representation, is_created=True)
