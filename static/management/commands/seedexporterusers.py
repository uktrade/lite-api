from json import loads as serialize

from django.db import transaction

from addresses.models import Address
from conf.constants import Roles
from conf.settings import env
from organisations.enums import OrganisationType
from organisations.models import Organisation, Site
from static.countries.helpers import get_country
from static.management.SeedCommand import SeedCommand
from users.enums import UserType
from users.models import ExporterUser, UserOrganisationRelationship, Role

DEFAULT_DEMO_ORG_NAME = "Archway Communications"
DEFAULT_DEMO_HMRC_ORG_NAME = "HMRC office at Battersea heliport"

DEFAULT_ORGANISATIONS = [
    {"name": DEFAULT_DEMO_ORG_NAME, "type": OrganisationType.COMMERCIAL, "reg_no": "09876543"},
    {"name": DEFAULT_DEMO_HMRC_ORG_NAME, "type": OrganisationType.HMRC, "reg_no": "75863840"},
]


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedexporterusers
    """

    help = "Seeds exporter users to organisations"
    info = "Seeding exporter users"
    success = "Successfully seeded exporter users"
    seed_command = "seedexporterusers"

    @transaction.atomic
    def operation(self, *args, **options):
        assert Role.objects.count(), "Role permissions must be seeded first!"

    @classmethod
    def seed_default_organisations(cls):
        for organisation in DEFAULT_ORGANISATIONS:
            org, _ = Organisation.objects.get_or_create(
                name=organisation["name"],
                type=organisation["type"],
                eori_number="1234567890AAA",
                sic_number="2345",
                vat_number="GB1234567",
                registration_number=organisation["reg_no"],
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

    @classmethod
    def seed_exporter_users(cls):
        for user in cls._get_users():
            default_data = dict(email=user["email"])

            exporter_user, created = ExporterUser.objects.get_or_create(
                email__iexact=default_data["email"], defaults=default_data
            )

            if created:
                cls.print_created_or_updated(ExporterUser, default_data, is_created=True)

            cls._add_exporter_to_default_organisations(user, exporter_user)

    @classmethod
    def _get_users(cls):
        admin_users = cls._get_users_from_env("INTERNAL_ADMIN_TEAM_USERS")
        exporter_users = cls._get_users_from_env("EXPORTER_USERS")

        # Declare admin users first, as they could be re-defined with an organisation + role in EXPORTER_USERS
        return [*admin_users, *exporter_users]

    @classmethod
    def _get_users_from_env(cls, env_variable):
        users = env(env_variable)
        # The JSON representation of the variable is different on environments, so it needs to be parsed first
        parsed_users = users.replace("=>", ":")

        try:
            serialized_users = serialize(parsed_users)
        except ValueError:
            raise ValueError(
                f"{env_variable} has incorrect format;"
                f"\nexpected format: [{{'email': '', 'organisation', 'role': ''}}]"
                f"\nbut got: {users}"
            )

        return serialized_users

    @classmethod
    def _add_exporter_to_default_organisations(cls, exporter_data, exporter_user: ExporterUser):
        for organisation in DEFAULT_ORGANISATIONS:
            role = Role.objects.get(
                name=exporter_data.get("role", Roles.EXPORTER_SUPER_USER_ROLE_NAME), type=UserType.EXPORTER
            )

            organisation = Organisation.objects.get(name=organisation["name"], type=organisation["type"])

            user_org_data = dict(user=exporter_user, organisation=organisation, role=role)

            user_org, created = UserOrganisationRelationship.objects.get_or_create(
                user=exporter_user, organisation=organisation, defaults=user_org_data
            )

            if created or user_org.role != role:
                user_org.role = role
                user_org.save()

                user_org_data = dict(
                    user=exporter_user.email,
                    organisation=dict(name=organisation.name, type=organisation.type, role=role.name),
                )
                cls.print_created_or_updated(UserOrganisationRelationship, user_org_data, is_created=created)
