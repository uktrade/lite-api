from json import loads as serialize

from django.db import transaction

from conf.settings import env
from organisations.enums import OrganisationType
from organisations.models import Organisation
from static.management.SeedCommand import SeedCommand
from static.management.commands.seeddemodata import DEFAULT_DEMO_HMRC_ORG_NAME, DEFAULT_DEMO_ORG_NAME
from static.management.commands.seedrolepermissions import ROLE_SUPER_USER_NAME
from static.management.commands.seedteams import ADMIN_TEAM_NAME
from teams.models import Team
from users.enums import UserType
from users.models import ExporterUser, UserOrganisationRelationship, Role, GovUser


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedusers
    """

    help = "Seeds gov and exporter users"
    info = "Seeding gov and exporter users"
    success = "Successfully seeded gov and exporter users"
    seed_command = "seedexporterusers"

    @transaction.atomic
    def operation(self, *args, **options):
        assert Team.objects.count(), "Teams must be seeded first!"
        assert Role.objects.count(), "Role permissions must be seeded first!"

        users = serialize(env("USERS"))

        for user in users:
            self.seed_gov_user(user)
            self.seed_exporter_user(user)

    @classmethod
    def seed_gov_user(cls, user_data):
        gov_data = user_data.get("internal")

        if gov_data:
            team = Team.objects.get(name=gov_data.get("team", ADMIN_TEAM_NAME))
            role = Role.objects.get(name=gov_data.get("role", ROLE_SUPER_USER_NAME), type=UserType.INTERNAL)

            gov_user, created = GovUser.objects.get_or_create(
                email__iexact=user_data["email"], defaults={"email": user_data["email"], "team": team, "role": role}
            )

            if created or gov_user.role != role or gov_user.team != team:
                gov_user.team = team
                gov_user.role = role
                gov_user.save()

                user_data = dict(email=user_data["email"], team=team.name, role=role.name)
                cls.print_created_or_updated(GovUser, user_data, is_created=created)

    @classmethod
    def seed_exporter_user(cls, user_data):
        exporter_data = user_data.get("exporter")

        if exporter_data:
            default_data = dict(email=user_data["email"])

            exporter_user, created = ExporterUser.objects.get_or_create(
                email__iexact=default_data["email"], defaults=default_data
            )

            if created:
                cls.print_created_or_updated(ExporterUser, default_data, is_created=True)

            cls._add_exporter_to_organisation(exporter_data, exporter_user)
            cls._add_exporter_to_default_hmrc_organisation(exporter_user)

    @classmethod
    def _add_exporter_to_organisation(cls, exporter_data, exporter_user: ExporterUser):
        role = Role.objects.get(name=exporter_data.get("role", ROLE_SUPER_USER_NAME), type=UserType.EXPORTER)

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
        hmrc_role = Role.objects.get(name=ROLE_SUPER_USER_NAME, type=UserType.EXPORTER)

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
