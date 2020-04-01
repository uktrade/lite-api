from django.db import transaction

from conf.constants import Roles
from organisations.enums import OrganisationType
from organisations.models import Organisation, Site
from organisations.tests.factories import OrganisationFactory, SiteFactory
from organisations.tests.providers import OrganisationProvider
from static.management.SeedCommand import SeedCommand

from faker import Faker

from test_helpers.helpers import create_exporter_users

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
        parser.add_argument("--type", help="Type of organisation to seed", type=str)
        parser.add_argument("--sites", help="Total number of sites to seed", type=int)
        parser.add_argument("--users", help="Total number of users to seed", type=int)

    @transaction.atomic
    def operation(self, *args, **options):
        org_name = options.get("name") or faker.company()
        org_type = options.get("type") or OrganisationType.COMMERCIAL
        no_of_sites = options.get("sites") or 1
        no_of_users = options.get("users") or 1

        self.seed_organisation(org_name, org_type, no_of_sites, no_of_users)

    @classmethod
    def seed_organisation(cls, org_name, org_type, no_of_sites, no_of_users):
        if not Organisation.objects.filter(name__iexact=org_name).exists():
            organisation = OrganisationFactory(name=org_name, type=org_type)

            exporter_users = [create_exporter_users(organisation, 1, role_id=Roles.EXPORTER_SUPER_USER_ROLE_ID)]
            # Since a Super User has already been created, subtract 1 from total number of users to seed
            exporter_users += create_exporter_users(organisation, no_of_users - 1)

            sites = [organisation.primary_site]
            # Since OrganisationFactory has already created a site, subtract 1 from total number of sites to seed
            sites += [SiteFactory(organisation=organisation) for _ in range(no_of_sites - 1)]

            cls._print_organisation_to_console(organisation, exporter_users[0])
            return [("organisation", organisation), ("sites", sites), ("exporter_users", exporter_users)]

    @classmethod
    def _print_organisation_to_console(cls, organisation, initial_org_user):
        organisation_representation = dict(
            id=str(organisation.id),
            primary_site_id=str(organisation.primary_site.id),
            initial_user_id=str(initial_org_user.id),
        )
        cls.print_created_or_updated(Organisation, organisation_representation, is_created=True)
