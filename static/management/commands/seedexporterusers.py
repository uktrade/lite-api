from json import loads as serialize
from django.db import transaction

from conf.constants import Roles
from conf.settings import env
from organisations.models import Organisation
from static.management.SeedCommand import SeedCommand
from static.management.commands.seedorganisations import HMRC_ORGANISATIONS, COMMERCIAL_ORGANISATIONS
from users.enums import UserType
from users.models import ExporterUser, UserOrganisationRelationship, Role


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedexporterusers
    """

    help = "Seeds exporter users"
    info = "Seeding exporter users"
    success = "Successfully seeded exporter users"
    seed_command = "seedexporterusers"

    @transaction.atomic
    def operation(self, *args, **options):
        self.seed_exporter_users()

    @classmethod
    def seed_exporter_users(cls):
        for exporter_user_data in cls._get_exporter_users():
            default_data = dict(email=exporter_user_data["email"])

            exporter_user, created = ExporterUser.objects.get_or_create(
                email__iexact=default_data["email"], defaults=default_data
            )

            if created:
                cls.print_created_or_updated(ExporterUser, default_data, is_created=True)

            cls._add_user_to_organisations(exporter_user, exporter_user_data)

    @classmethod
    def _get_exporter_users(cls):
        admin_users = cls._parse_users("INTERNAL_ADMIN_TEAM_USERS")
        exporter_users = cls._parse_users("EXPORTER_USERS")

        # Add INTERNAL_ADMIN_TEAM_USERS to exporter_users list if they have not been defined in EXPORTER_USERS
        admin_user_emails = [admin_user["email"] for admin_user in admin_users]
        exporter_user_emails = [exporter_user["email"] for exporter_user in exporter_users]
        for email in admin_user_emails:
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
                f'\nexpected format: [{{"email": "", "organisation": "", "role": ""}}]'
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
            cls._add_user_to_organisation(exporter_user, organisation, role_name)
        else:
            for organisation in COMMERCIAL_ORGANISATIONS:
                cls._add_user_to_organisation(exporter_user, organisation, role_name)

        for organisation in HMRC_ORGANISATIONS:
            cls._add_user_to_organisation(exporter_user, organisation, Roles.EXPORTER_SUPER_USER_ROLE_NAME)

    @classmethod
    def _get_organisation_from_commercial_organisations(cls, organisation_name):
        organisations = [
            organisation for organisation in COMMERCIAL_ORGANISATIONS if organisation["name"] == organisation_name
        ]
        return organisations[0] if organisations else None

    @classmethod
    def _add_user_to_organisation(cls, exporter_user: ExporterUser, organisation, role_name):
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
