from json import loads as serialize

from django.db import transaction

from api.addresses.models import Address
from api.core.constants import Roles
from api.conf.settings import env
from api.organisations.enums import OrganisationType, OrganisationStatus
from api.organisations.models import Organisation, Site
from api.staticdata.countries.helpers import get_country
from api.staticdata.management.SeedCommand import SeedCommand
from api.users.enums import UserType
from api.users.models import ExporterUser, UserOrganisationRelationship, Role

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
    pipenv run ./manage.py seedexporterusers
    """

    help = "Seeds exporter users to organisations"
    info = "Seeding exporter users"
    seed_command = "seedexporterusers"

    @transaction.atomic
    def operation(self, *args, **options):
        self.seed_default_organisations()
        self.seed_exporter_users()

    @classmethod
    def seed_default_organisations(cls):
        for organisation in COMMERCIAL_ORGANISATIONS + HMRC_ORGANISATIONS:
            org, created = Organisation.objects.get_or_create(
                name__iexact=organisation["name"],
                defaults={
                    "name": organisation["name"],
                    "type": organisation["type"],
                    "eori_number": "1234567890AAA",
                    "sic_number": "2345",
                    "vat_number": "GB123456789",
                    "registration_number": organisation["reg_no"],
                    "status": OrganisationStatus.ACTIVE,
                },
            )

            if created:
                address = Address.objects.create(
                    address_line_1="42 Question Road",
                    address_line_2="",
                    country=get_country("GB"),
                    city="London",
                    region="Greater London",
                    postcode="SW1A 0AA",
                )

                site = Site.objects.create(name="Headquarters", organisation=org, address=address)
                site.site_records_located_at = site
                site.save()
                org.primary_site = site
                org.save()

                cls.print_created_or_updated(
                    Organisation, {"name": organisation["name"], "type": organisation["type"]}, is_created=True,
                )

    @classmethod
    def seed_exporter_users(cls):
        for exporter_user_data in cls._get_exporter_users():
            email = exporter_user_data["email"]

            exporter_user, created = ExporterUser.objects.get_or_create(email__iexact=email, defaults={"email": email})

            if created:
                cls.print_created_or_updated(ExporterUser, {"email": email}, is_created=True)

            cls._add_user_to_organisations(exporter_user, exporter_user_data)

    @classmethod
    def _get_exporter_users(cls):
        admin_users = cls._parse_users("INTERNAL_USERS")
        exporter_users = cls._parse_users("EXPORTER_USERS")
        exporter_user_emails = [exporter_user["email"] for exporter_user in exporter_users]

        # Add INTERNAL_USERS to exporter_users list if they have not been defined in EXPORTER_USERS
        for user in admin_users:
            email = user["email"]

            if email not in exporter_user_emails:
                exporter_users.append({"email": email})

        return exporter_users

    @classmethod
    def _parse_users(cls, env_variable):
        users = env(env_variable)
        # The JSON representation of the variable is different on environments, so it needs to be parsed first
        parsed_users = users.replace("=>", ":")

        try:
            parsed_users = serialize(parsed_users)
        except ValueError:
            raise ValueError(
                f"{env_variable} has incorrect format;"
                f'\nexpected format: [{{"email": "", "organisation": "", role": ""}}]'
                f"\nbut got: {users}"
            )

        return parsed_users

    @classmethod
    def _add_user_to_organisations(cls, exporter_user: ExporterUser, exporter_user_data):
        role_name = exporter_user_data.get("role", Roles.EXPORTER_SUPER_USER_ROLE_NAME)
        organisation_name = exporter_user_data.get("organisation")

        # If a commercial (non-HMRC) Organisation was specified, only seed the user to that chosen organisation
        if organisation_name:
            organisation = cls._get_organisation_from_commercial_organisations(organisation_name)
            cls._add_exporter_to_organisation(exporter_user, organisation, role_name)
        else:
            for organisation in COMMERCIAL_ORGANISATIONS:
                cls._add_exporter_to_organisation(exporter_user, organisation, role_name)

        for organisation in HMRC_ORGANISATIONS:
            cls._add_exporter_to_organisation(exporter_user, organisation, Roles.EXPORTER_SUPER_USER_ROLE_NAME)

    @classmethod
    def _get_organisation_from_commercial_organisations(cls, organisation_name):
        organisations = [
            organisation for organisation in COMMERCIAL_ORGANISATIONS if organisation["name"] == organisation_name
        ]
        return organisations[0] if organisations else None

    @classmethod
    def _add_exporter_to_organisation(cls, exporter_user: ExporterUser, organisation, role_name):
        role = Role.objects.get(name=role_name, type=UserType.EXPORTER)
        org = Organisation.objects.get(name=organisation["name"], type=organisation["type"])

        user_org, created = UserOrganisationRelationship.objects.get_or_create(
            user=exporter_user, organisation=org, defaults=dict(user=exporter_user, organisation=org, role=role)
        )

        if created or user_org.role != role:
            user_org.role = role
            user_org.save()

            user_org_data = dict(
                user=exporter_user.email, organisation=dict(name=org.name, type=org.type, role=role.name),
            )
            cls.print_created_or_updated(UserOrganisationRelationship, user_org_data, is_created=created)
