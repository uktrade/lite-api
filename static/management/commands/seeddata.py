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


class Command(SeedCommand):
    """
    pipenv run ./manage.py seeddata --action ...>
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
        parser.add_argument("--sites-max", help="max number of sites", type=int)
        parser.add_argument("--sites-min", help="min number of sites", type=int)
        parser.add_argument("--users-min", help="number of users", type=int)
        parser.add_argument("--users-max", help="number of users", type=int)
        parser.add_argument("--user-email", help="user email", type=str)
        parser.add_argument("--max-goods", help="max number of goods", type=int)
        parser.add_argument("--applications", help="number of applications", type=int)

    def operation(self, *args, **options):
        action = options.get("action")
        if action is None:
            raise Exception("action not specified!")
        self.stdout.write(self.style.SUCCESS(f"action = {action}"))

        if action == "org":
            org_count = self.get_arg(options, "organisations", 1)
            site_max = self.get_arg(options, "site_max", 1)
            site_min = self.get_arg(options, "site_min", 1)
            user_min = self.get_arg(options, "user_min", 1)
            user_max = self.get_arg(options, "user_max", 1)
            user_email = self.get_arg(options, "user_email", 1)

            # ensure the correct number of organisations
            organisations, created_count = self.get_create_organisations(org_count, user_email, site_min, site_max)

            # ensure the correct number of users
            user_counts = [
                len(self.organisation_get_create_users(organisation, user_max, user_min))
                for organisation in organisations
            ]

            print(
                f"Ensured that at least {len(organisations)} organisations exist"
                f", added {created_count} new organisations"
            )
            print(f"each with between {user_min} and {user_max} users, added {sum(user_counts)} new users")

            return organisations

        if action == "users":
            print("Add users to organisations")
            org_count = self.get_arg(options, "organisations", 1)
            user_min = self.get_arg(options, "users_min", 1)
            user_max = self.get_arg(options, "users_max", 1)

            # ensure the correct number of organisations
            organisations = self.organisation_get_first_n(org_count)

            # ensure the correct number of users
            user_counts = [
                len(self.organisation_get_create_users(organisation, user_max, user_min))
                for organisation in organisations
            ]

            print(f"each with between {user_min} and {user_max} users, added {sum(user_counts)} new users")
            return

        if action == "site":
            return

        if action == "add-user":
            org = self.get_arg(options, "organisation")
            user_email = self.get_arg(options, "user_email")
            exporter_user = ExporterUser.objects.get_or_create(first_name="first", last_name="last", email=user_email)

            to_add = []
            if org == "all":
                membership = (
                    UserOrganisationRelationship.objects.select_related("organisation")
                        .filter(user=exporter_user)
                        .values_list("organisation__id")
                )
                organisations = Organisation.objects.all()
                ids_to_add = set([org.id for org in organisations]) - set(membership)
                to_add = [org for id_to_add in ids_to_add for org in organisations if org.id == id_to_add]
            else:
                organisation = Organisation.objects.get(id=UUID(org))
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
            org = self.get_arg(options, "organisation")
            user_email = self.get_arg(options, "user_email")
            exporter_user = ExporterUser.objects.get_or_create(first_name="first", last_name="last", email=user_email)

            if org == "all":
                count, _ = self.organisation_delete_user_from_all(exporter_user=exporter_user)
            else:
                organisation = Organisation.objects.get(id=UUID(org))
                count, _ = self.organisation_delete_user(organisation=organisation, exporter_user=exporter_user)

            self.stdout.write(self.style.SUCCESS(f"Removed {exporter_user.email} from {count} organisations"))
            return

        if action == "siel":
            print("Add SIEL applications to organisations")
            org_count = self.get_arg(options, "organisations", 1)
            app_count = self.get_arg(options, "applications", 1)
            max_goods = self.get_arg(options, "max_goods", 1)

            # ensure the correct number of organisations
            organisations = self.organisation_get_first_n(org_count)

            # ensure the correct number of standard applications per org
            org_app_counts = [
                (org, StandardApplication.objects.filter(organisation_id=org.id).count())
                for org in organisations
            ]
            applications_to_add = [(org, app_count - count) for org, count in org_app_counts if count < app_count]
            apps = [
                self.app_factory(org=org, max_goods_to_use=max_goods, applications_to_add=apps_to_add)
                for org, apps_to_add in applications_to_add
            ]
            print(f"ensured {app_count} applications for the first {org_count} organisations")
            print(f"added {sum(apps)} applications in total")
            return apps

    def organisation_get_first_n(self, org_count):
        organisations = list(Organisation.objects.all())
        if len(organisations) < org_count:
            error_str = f"not enough organisations, found: {len(organisations)} of {org_count} required"
            self.stdout.write(self.style.ERROR(error_str))
            raise Exception(error_str)
        return organisations

    def organisation_get_create_users(self, organisation, user_max, user_min):
        current_users = UserOrganisationRelationship.objects.filter(organisation=organisation)
        if len(current_users) <= user_min:
            return current_users

        required_users_count = random.randint(user_min, user_max) - current_users
        company_domain = organisation.name.replace(" ", "").replace("'", "").replace(",", "").replace("-", "")
        added = self.organisation_create_random_users(company_domain, organisation, required_users_count)
        return required_users_count + added

    def get_create_organisations(self, org_count, org_primary, org_site_min, org_site_max):
        organisations = list(Organisation.objects.all()[:org_count])
        required = max(0, org_count - len(organisations))
        created_organisations = [self.org_factory(org_primary, org_site_min, org_site_max) for _ in range(0, required)]
        return organisations + created_organisations, len(created_organisations)

    @staticmethod
    def get_arg(options, name, default=None):
        var = options.get(name) or default
        if var is None:
            raise Exception(f"{name} not specified!")
        print(f"{name}={var}")
        return var

    @staticmethod
    def organisation_create_random_users(company_email_domain, organisation, required_users_count):
        added = list()
        for _ in range(required_users_count):
            first_name = faker.first_name()
            last_name = faker.last_name()
            role_id = Roles.EXPORTER_SUPER_USER_ROLE_ID
            email = f"{first_name}.{last_name}@{company_email_domain}.co.uk"
            user, created = ExporterUser.objects.get_or_create(first_name=first_name, last_name=last_name, email=email)
            new_org_user = UserOrganisationRelationship(user=user, organisation=organisation, role_id=role_id)
            new_org_user.save()
            added.append(new_org_user)
        return added

    @staticmethod
    def org_factory(org_primary, org_site_min, org_site_max):
        org_name = faker.company()
        if Organisation.objects.filter(name__iexact=org_name).exists():
            idx = 1
            new_name = f"{org_name} ({idx})"
            while Organisation.objects.filter(name__iexact=new_name).exists():
                idx += 1
                new_name = f"{org_name} ({idx})"
            org_name = new_name

        organisation, _, _, _ = OrgCommand.seed_organisation(
            org_name, OrganisationType.COMMERCIAL, random.randint(org_site_min, org_site_max), 1, org_primary,
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
            return UserOrganisationRelationship.objects.filter(user=exporter_user, organisation=organisation).delete()
        except Exception:
            return 0, None

    @staticmethod
    def app_factory(org, applications_to_add, max_goods_to_use):
        _, submitted_applications, _ = AppCommand.seed_siel_applications(org, applications_to_add, max_goods_to_use, )
        return len(submitted_applications)
