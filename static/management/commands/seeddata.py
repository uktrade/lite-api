import random
from uuid import UUID

from faker import Faker

from applications.models import StandardApplication
from conf.constants import Roles
from organisations.enums import OrganisationType
from organisations.models import Organisation
from organisations.tests.providers import OrganisationProvider
from static.management.SeedCommand import SeedCommand
from static.management.commands.seedapplication import Command as AppCommand
from static.management.commands.seedorganisation import Command as OrgCommand
from users.models import UserOrganisationRelationship, ExporterUser

faker = Faker()
faker.add_provider(OrganisationProvider)


class Params(object):
    pass


# class Command(SeedCommand):
#     """
#     pipenv run ./manage.py seeddata>
#     """
#
#     help = "Seeds data"
#     info = "Seeding data"
#     success = "Successfully seeded data"
#     seed_command = "data-org"
#
#     def add_arguments(self, parser):
#         parser.add_argument("--count", help="the number of organisations", type=int)
#
#     def orgs_and_apps(self, options):
#         self.stdout.write(self.style.SUCCESS(f"adding {options.get('org_count') or 1} orgs")


class Command(SeedCommand):
    """
    pipenv run ./manage.py seeddata>
    """

    help = "Seeds data"
    info = "Seeding data"
    success = "Successfully completed action"
    seed_command = "seeddata"

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            "--action", help="command", choices=["org", "site", "remove-user", "add-user", "siel"], type=str
        )
        parser.add_argument("--organisation", help="application count", type=str)
        parser.add_argument("--organisations", help="application count", type=int)
        parser.add_argument("--site-max", help="max number of sites", type=int)
        parser.add_argument("--site-min", help="min number of sites", type=int)
        parser.add_argument("--user-min", help="number of users", type=int)
        parser.add_argument("--user-max", help="number of users", type=int)
        parser.add_argument("--user-email", help="user email", type=str)
        parser.add_argument("--max-goods", help="max number of goods", type=int)
        parser.add_argument("--applications", help="number of applications", type=int)

    def operation(self, *args, **options):
        action = options.get("action")

        if action is None:
            raise Exception("action not specified!")

        self.stdout.write(self.style.SUCCESS(f"action = {action}"))

        if action == "org":
            org_count = options.get("organisations") or 1
            site_max = options.get("site_max") or 1
            site_min = options.get("site_min") or 1
            user_min = options.get("user_min") or 1
            user_max = options.get("user_max") or 1
            user_email = options.get("user_email")
            print(f"organisations={org_count}")
            print(f"site_max={site_max}")
            print(f"site_min={site_min}")
            print(f"user_min={user_min}")
            print(f"user_max={user_max}")
            print(f"primary_email={user_email}")

            # ensure the correct number of organisations
            organisations = self.get_create_organisations(org_count, user_email, site_min, site_max, user_min, user_max)
            print(f"Ensured that at least {len(organisations)} organisations exist")
            return organisations

        if action == "site":
            return

        if action == "add-user":
            org, exporter_user, organisation = self.parse_user_options(options)
            to_add = []

            if org == "all":
                organisations = Organisation.objects.all()
                membership_ids = (
                    UserOrganisationRelationship.objects.select_related("organisation")
                    .filter(user=exporter_user)
                    .values_list("organisation__id")
                )
                ids_to_add = set([org.id for org in organisations]) - set(membership_ids)
                to_add = [org for id_to_add in ids_to_add for org in organisations if org.id == id_to_add]
            else:
                user = self.organisation_get_user(organisation, exporter_user)
                if user is None:
                    to_add.append(organisation)

            added_users = [
                self.organisation_add_user(organisation=organisation, exporter_user=exporter_user)
                for organisation in to_add
            ]

            self.stdout.write(self.style.SUCCESS(f"Added {exporter_user.email} to {len(added_users)} organisations"))
            return

        if action == "remove-user":
            org, exporter_user, organisation = self.parse_user_options(options)

            if org == "all":
                count, _ = self.organisation_delete_user_from_all(exporter_user=exporter_user)
            else:
                count, _ = self.organisation_delete_user(organisation=organisation, exporter_user=exporter_user)

            self.stdout.write(self.style.SUCCESS(f"Removed {exporter_user.email} from {count} organisations"))
            return

        if action == "siel":
            org_count = options.get("organisations") or 1
            app_count = options.get("applications") or 0
            max_goods = options.get("max_goods") or 1

            print("Add SIEL applications to organisations")
            print(f"organisations={app_count}")
            print(f"applications={app_count}")
            print(f"max_goods={max_goods}")

            # ensure the correct number of organisations
            organisations = list(Organisation.objects.all())
            if len(organisations) < org_count:
                error_str = f"not enough organisations, found: {len(organisations)} of {org_count} required"
                self.stdout.write(self.style.ERROR(error_str))
                raise Exception(error_str)

            # ensure the correct number of standard applications per org
            org_app_counts = [
                (org, StandardApplication.objects.filter(organisation_id=org.id).count()) for org in organisations
            ]
            applications_to_add = [(org, app_count - count) for org, count in org_app_counts if count < app_count]
            apps = [
                self.app_factory(org=org, max_goods_to_use=max_goods, applications_to_add=apps_to_add)
                for org, apps_to_add in applications_to_add
            ]
            print(f"ensured {app_count} applications for the first {org_count} organisations")
            print(f"added {sum(apps)} applications in total")
            return apps

    def parse_user_options(self, options):
        org = options.get("organisation")
        user_email = options.get("user_email")

        if org is None:
            raise Exception("organisation not specified!")

        if user_email is None:
            raise Exception("user email not specified!")
        try:
            exporter_user = ExporterUser.objects.get(email__exact=user_email)
        except ExporterUser.DoesNotExist:
            raise Exception(f"An Exporter User with email: '{user_email}' does not exist")

        organisation = None
        if org != "all":
            try:
                organisation = Organisation.objects.get(id=UUID(org))
            except Organisation.DoesNotExist:
                raise Exception(f"An Organisation with id: '{org}' does not exist")

        return org, exporter_user, organisation

    def get_create_organisations(self, org_count, org_primary, org_site_min, org_site_max, org_user_min, org_user_max):
        organisations = list(Organisation.objects.all()[:org_count])
        required = max(0, org_count - len(organisations))
        organisations += [
            self.org_factory(org_primary, org_site_min, org_site_max, org_user_min, org_user_max)
            for _ in range(0, required)
        ]
        return organisations

    @staticmethod
    def org_factory(org_primary, org_site_min, org_site_max, org_user_min, org_user_max):
        org_name = faker.company()
        if Organisation.objects.filter(name__iexact=org_name).exists():
            idx = 1
            new_name = f"{org_name} ({idx})"
            while Organisation.objects.filter(name__iexact=new_name).exists():
                idx += 1
                new_name = f"{org_name} ({idx})"
            org_name = new_name

        organisation, _, _, _ = OrgCommand.seed_organisation(
            org_name,
            OrganisationType.COMMERCIAL,
            random.randint(org_site_min, org_site_max),
            random.randint(org_user_min, org_user_max),
            org_primary,
        )
        return organisation

    @staticmethod
    def organisation_add_user(organisation, exporter_user, role_id=Roles.EXPORTER_SUPER_USER_ROLE_ID):
        return UserOrganisationRelationship.objects.create(
            organisation=organisation, user=exporter_user, role_id=role_id
        )

    @staticmethod
    def organisation_get_user(organisation, exporter_user):
        try:
            return UserOrganisationRelationship.objects.get(user=exporter_user, organisation=organisation)
        except UserOrganisationRelationship.DoesNotExist:
            return None

    @staticmethod
    def organisation_delete_user_from_all(exporter_user):
        return UserOrganisationRelationship.objects.select_related("organisation").filter(user=exporter_user).delete()

    @staticmethod
    def organisation_delete_user(organisation, exporter_user):
        try:
            return UserOrganisationRelationship.objects.filter(
                user=exporter_user, organisation=organisation
            ).delete()
        except Exception:
            return 0, None

    @staticmethod
    def app_factory(org, applications_to_add, max_goods_to_use):
        _, submitted_applications, _ = AppCommand.seed_siel_applications(org, applications_to_add, max_goods_to_use,)
        return len(submitted_applications)
