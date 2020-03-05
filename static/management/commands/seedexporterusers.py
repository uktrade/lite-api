from json import loads as serialize
from django.db import transaction

from conf.constants import Roles
from conf.settings import env
from organisations.enums import OrganisationType
from organisations.models import Organisation
from static.management.SeedCommand import SeedCommand
from static.management.commands.seeddemodata import DEFAULT_DEMO_HMRC_ORG_NAME, DEFAULT_DEMO_ORG_NAME
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
        assert (
            Organisation.objects.filter(name=DEFAULT_DEMO_ORG_NAME).exists()
            and Organisation.objects.filter(name=DEFAULT_DEMO_HMRC_ORG_NAME).exists()
        ), "Demo organisations must be seeded first!"
        assert Role.objects.count(), "Role permissions must be seeded first!"

        # Seed admin users first, as they could be re-defined with a role in the EXPORTER_USERS environment variable
        self.seed_exporter_users(self._get_admin_users())
        self.seed_exporter_users(self._get_exporter_users())

    @classmethod
    def _get_exporter_users(cls):
        return cls._get_users_list("EXPORTER_USERS")

    @classmethod
    def _get_admin_users(cls):
        admin_users = cls._get_users_list("INTERNAL_ADMIN_TEAM_USERS")
        # seed admin users as an exporter super-user
        for user in admin_users:
            user["role"] = Roles.EXPORTER_SUPER_USER_ROLE_NAME
        return admin_users

    @classmethod
    def _get_users_list(cls, env_variable):
        users = env(env_variable)
        # The JSON representation of the variable is different on environments, so it needs to be parsed first
        parsed_users = users.replace("=>", ":")

        try:
            serialized_users = serialize(parsed_users)
        except ValueError:
            raise ValueError(
                f"{env_variable} has incorrect format;"
                f"\nexpected format: [{{'email': '', 'role': ''}}]"
                f"\nbut got: {users}"
            )

        return serialized_users

    @classmethod
    def seed_exporter_users(cls, users):
        for user in users:
            default_data = dict(email=user["email"])

            exporter_user, created = ExporterUser.objects.get_or_create(
                email__iexact=default_data["email"], defaults=default_data
            )

            if created:
                cls.print_created_or_updated(ExporterUser, default_data, is_created=True)

            cls._add_exporter_to_organisation(user, exporter_user)
            cls._add_exporter_to_default_hmrc_organisation(exporter_user)

    @classmethod
    def _add_exporter_to_organisation(cls, exporter_data, exporter_user: ExporterUser):
        role = Role.objects.get(
            name=exporter_data.get("role", Roles.EXPORTER_SUPER_USER_ROLE_NAME), type=UserType.EXPORTER
        )

        organisation = Organisation.objects.get(
            name=exporter_data.get("organisation", DEFAULT_DEMO_ORG_NAME), type=OrganisationType.COMMERCIAL
        )

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

    @classmethod
    def _add_exporter_to_default_hmrc_organisation(cls, exporter_user: ExporterUser):
        hmrc_role = Role.objects.get(name=Roles.EXPORTER_SUPER_USER_ROLE_NAME, type=UserType.EXPORTER)

        hmrc_org = Organisation.objects.get(name=DEFAULT_DEMO_HMRC_ORG_NAME, type=OrganisationType.HMRC)

        user_hmrc_org_data = dict(user=exporter_user, organisation=hmrc_org, role=hmrc_role)

        _, created = UserOrganisationRelationship.objects.get_or_create(
            user=exporter_user, organisation=hmrc_org, defaults=user_hmrc_org_data
        )

        if created:
            user_hmrc_org_data = dict(
                user=exporter_user.email,
                organisation=dict(name=hmrc_org.name, type=hmrc_org.type, role=hmrc_role.name),
            )
            cls.print_created_or_updated(UserOrganisationRelationship, user_hmrc_org_data, is_created=created)
