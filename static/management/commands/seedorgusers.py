from json import loads as serialize

from django.db import transaction

from addresses.models import Address
from conf.settings import env
from organisations.enums import OrganisationType
from organisations.models import Organisation, Site
from static.countries.helpers import get_country
from static.countries.models import Country
from static.management.SeedCommand import SeedCommand
from users.models import ExporterUser, UserOrganisationRelationship, Role


ORGANISATIONS = [
    {"name": "Archway Communications", "type": OrganisationType.COMMERCIAL, "reg_no": "09876543",},
    {"name": "HMRC office at Battersea heliport", "type": OrganisationType.HMRC, "reg_no": "75863840",},
]


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedorgusers
    """

    help = "Seeds test organisation users"
    info = "Seeding org users"
    success = "Successfully seeded org users"
    seed_command = "seedorgusers"

    @transaction.atomic
    def operation(self, *args, **options):
        assert Role.objects.count(), "Role permissions must be seeded first!"
        assert Country.objects.count(), "Countries must be seeded first!"

        for org in ORGANISATIONS:
            organisation = seed_organisation(org)
            _seed_exporter_users_to_organisation(organisation)


def seed_organisation(org):
    organisation = Organisation.objects.get_or_create(
        name=org["name"],
        type=org["type"],
        eori_number="1234567890AAA",
        sic_number="2345",
        vat_number="GB1234567",
        registration_number=org["reg_no"],
    )[0]

    seed_organisation_site(organisation)
    return organisation


def seed_organisation_site(organisation: Organisation):
    address = Address.objects.get_or_create(
        address_line_1="42 Question Road",
        address_line_2="",
        country=get_country("GB"),
        city="London",
        region="London",
        postcode="Islington",
    )[0]
    site = Site.objects.get_or_create(name="Headquarters", organisation=organisation, address=address)[0]
    organisation.primary_site = site
    organisation.save()


def _seed_exporter_users_to_organisation(organisation: Organisation):
    # Do not combine the TEST_EXPORTER_USERS and SEED_USERS env variables in `.env`;
    # this would grant GOV user permissions to the exporter test-user accounts.
    for email in _get_exporter_users():
        exporter_user = _create_exporter_user(email)
        _add_user_to_organisation(exporter_user, organisation)


def _get_exporter_users():
    test_exporter_users = serialize(env("TEST_EXPORTER_USERS"))
    seed_users = serialize(env("SEED_USERS"))
    return test_exporter_users + seed_users


def _create_exporter_user(exporter_user_email: str):
    first_name, last_name = _extract_names_from_email(exporter_user_email)
    exporter_user_data = dict(email=exporter_user_email, first_name=first_name, last_name=last_name)

    exporter_user, created = ExporterUser.objects.get_or_create(
        email__iexact=exporter_user_email, defaults=exporter_user_data
    )

    if created:
        print(f"CREATED ExporterUser: {exporter_user_data}")

    return exporter_user


def _extract_names_from_email(exporter_user_email: str):
    email = exporter_user_email.split("@")
    full_name = email[0].split(".")
    first_name = full_name[0]
    last_name = full_name[1] if len(full_name) > 1 else email[1]
    return first_name.capitalize(), last_name.capitalize()


def _add_user_to_organisation(user: ExporterUser, organisation: Organisation):
    user_org = UserOrganisationRelationship.objects.filter(user=user, organisation=organisation)

    if not user_org.exists():
        user_org_data = dict(email=user.email, organisation=organisation.name)
        UserOrganisationRelationship.objects.create(user=user, organisation=organisation)
        print(f"CREATED UserOrganisationRelationship: {user_org_data}")
