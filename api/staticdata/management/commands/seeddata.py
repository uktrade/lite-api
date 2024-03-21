import multiprocessing
import random
from time import perf_counter
from uuid import UUID

from django import db
from faker import Faker

from api.applications.models import StandardApplication, GoodOnApplication
from api.flags.models import Flag
from api.core.constants import Roles
from api.goods.models import Good
from api.organisations.enums import OrganisationType
from api.organisations.models import Organisation, Site
from api.organisations.tests.factories import SiteFactory
from api.organisations.tests.providers import OrganisationProvider
from api.queries.end_user_advisories.models import EndUserAdvisoryQuery
from api.staticdata.management.SeedCommand import SeedCommand
from api.staticdata.management.commands.seedapplications import Command as AppCommand
from api.staticdata.management.commands.seedorganisation import Command as OrgCommand
from test_helpers.clients import DataTestClient
from api.users.models import UserOrganisationRelationship, ExporterUser

faker = Faker()
faker.add_provider(OrganisationProvider)


class ActionBase:
    @staticmethod
    def organisation_get_first_n(org_count):
        organisations = list(Organisation.objects.all())
        if len(organisations) < org_count:
            error_str = f"not enough organisations, found: {len(organisations)} of {org_count} required"
            raise Exception(error_str)
        return organisations[:org_count]

    def organisation_get_create_users(self, organisation, user_max, user_min):
        current_users = list(UserOrganisationRelationship.objects.filter(organisation=organisation))
        if len(current_users) >= user_min:
            return current_users, []

        required_users_count = random.randint(user_min, user_max) - len(current_users)
        company_domain = organisation.name.replace(" ", "").replace("'", "").replace(",", "").replace("-", "")
        created_users = self.organisation_create_random_users(company_domain, organisation, required_users_count)
        return current_users + created_users, created_users

    @staticmethod
    def get_arg(options, name, default=None, required=True):
        var = options.get(name)
        if var is None:
            var = default
        if (var is None) and required:
            raise Exception(f"{name} not specified!")
        print(f"{name}={var}")
        return var

    @staticmethod
    def get_min_max_arg(options):
        min_value = ActionBase.get_arg(options, "min", 1)
        max_value = ActionBase.get_arg(options, "max", 1)
        max_value = max(min_value, max_value)
        return min_value, max_value

    @staticmethod
    def organisation_create_random_users(company_email_domain, organisation, required_users_count):
        added = list()
        role_id = Roles.EXPORTER_ADMINISTRATOR_ROLE_ID
        for _ in range(required_users_count):
            email, first_name, last_name = ActionBase.fake_export_user_details(company_email_domain)
            user, _ = ExporterUser.objects.get_or_create(first_name=first_name, last_name=last_name, email=email)
            new_org_user = UserOrganisationRelationship.objects.create(
                user=user, organisation=organisation, role_id=role_id
            )
            added.append(new_org_user)
        return added

    @staticmethod
    def fake_export_user_details(company_email_domain):
        first_name = faker.first_name()
        last_name = faker.last_name()
        return f"{first_name}.{last_name}@{company_email_domain}.co.uk", first_name, last_name

    @staticmethod
    def org_factory(org_primary, org_site_min, org_site_max):
        root_name = faker.company()
        idx = 1
        org_name = root_name
        while idx < 100:
            try:
                organisation, _, _, _ = OrgCommand.seed_organisation(
                    org_name,
                    OrganisationType.COMMERCIAL,
                    random.randint(org_site_min, org_site_max),
                    1,
                    org_primary,
                )
                return organisation
            except ValueError:
                org_name = f"{root_name} ({idx})"
                idx += 1
        return None

    @staticmethod
    def organisation_get_create_user(organisation, exporter_user, role_id=Roles.EXPORTER_ADMINISTRATOR_ROLE_ID):
        return UserOrganisationRelationship.objects.get_or_create(
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
        return UserOrganisationRelationship.objects.filter(user=exporter_user, organisation=organisation).delete()

    @staticmethod
    def app_factory(org, applications_to_add, max_goods_to_use):
        _, submitted_applications, _ = AppCommand.seed_siel_applications(
            org,
            applications_to_add,
            max_goods_to_use,
        )
        return len(submitted_applications)

    @staticmethod
    def organisation_get_create_goods(organisation, goods_count):
        goods, goods_added = AppCommand.ensure_verified_goods_exist(
            organisation=organisation, number_of_goods=goods_count
        )
        return goods, goods_added

    @staticmethod
    def organisation_get_create_sites(organisation, site_count) -> (list, int):
        sites = Site.objects.filter(organisation=organisation)
        existing_sites = len(sites)
        if existing_sites >= site_count:
            return sites, 0
        added = [SiteFactory(organisation=organisation) for _ in range(site_count - existing_sites)]
        return list(sites) + added, len(added)

    @staticmethod
    def do_work(args):
        return args[0](*args[1:])

    @staticmethod
    def get_mapper(mt):
        mapper = map
        if mt is not None:
            db.connections.close_all()
            processes = mt if mt > 0 else None
            pool = multiprocessing.Pool(processes=processes)
            mapper = pool.map
        return mapper


class ActionOrg(ActionBase):
    def action(self, options):
        org_count = self.get_arg(options, "count", 1)
        org_site_min, org_site_max = self.get_min_max_arg(options)
        org_primary = self.get_arg(options, "email", required=False)
        mt = self.get_arg(options, "mt", required=False)

        organisations = list(Organisation.objects.all()[:org_count])
        required = max(0, org_count - len(organisations))

        job_args = [(ActionBase.org_factory, org_primary, org_site_min, org_site_max) for _ in range(0, required)]
        created_organisations = [org for org in self.get_mapper(mt)(ActionBase.do_work, job_args)]

        print(
            f"Ensured that at least {org_count} organisations exist"
            f", added {len(created_organisations)} new organisations"
        )
        return organisations + created_organisations


class ActionAddFakeUsers(ActionBase):
    def action(self, options):
        print("Add fake export users to organisations")
        user_min, user_max = self.get_min_max_arg(options)
        org_count = self.get_arg(options, "count", 1)
        uuid = self.get_arg(options, "uuid", required=False)
        organisations = [Organisation.objects.get(id=UUID(uuid))] if uuid else self.organisation_get_first_n(org_count)

        # ensure the correct number of users
        users = [self.organisation_get_create_users(organisation, user_max, user_min) for organisation in organisations]
        added_counts = [len(added) for _, added in users]

        print(
            f"{len(organisations)} organisations"
            f" each have between {user_min} and {user_max} users, added {sum(added_counts)} new users"
        )
        return


class ActionEndUserAdvisory(ActionBase):
    tc = DataTestClient()

    def action(self, options):
        print("Add End User Advisory query to organisations")
        org_count = self.get_arg(options, "count", 1)
        uuid = self.get_arg(options, "uuid", required=False)
        mt = self.get_arg(options, "mt", required=False)

        organisations = [Organisation.objects.get(id=UUID(uuid))] if uuid else self.organisation_get_first_n(org_count)
        org_eua_data = [
            org["organisation_id"]
            for org in EndUserAdvisoryQuery.objects.order_by().values("organisation_id").distinct()
        ]
        orgs = [org for org in organisations if org.id not in org_eua_data]

        jobs = [(self.add_end_user_advisory, organisation) for organisation in orgs]
        results = [application for application in self.get_mapper(mt)(ActionBase.do_work, jobs)]

        print(f"Added an end user advisory for {org_count} organisations, added {len(results)} EUA's in total")
        return results

    def add_end_user_advisory(self, organisation):
        self.tc.exporter_user = random.choice(organisation.get_users())
        self.tc.organisation = organisation
        return self.tc.create_end_user_advisory(note="a note", reasoning="a reason", organisation=organisation)


class ActionUser(ActionBase):
    def action(self, options):
        org_uuid = self.get_arg(options, "uuid")
        user_email = self.get_arg(options, "email")
        exporter_user, _ = ExporterUser.objects.get_or_create(email=user_email)
        action_method = self.remove if self.get_arg(options, "remove") else self.add
        action_method(org_uuid, exporter_user)

    def add(self, org_uuid, exporter_user):
        to_add = []
        if org_uuid == "all":
            membership = (
                UserOrganisationRelationship.objects.select_related("organisation")
                .filter(user=exporter_user)
                .values_list("organisation_id")
            )
            organisations = Organisation.objects.all()
            ids_to_add = set([org.id for org in organisations]) - set(membership)
            to_add = [org for id_to_add in ids_to_add for org in organisations if org.id == id_to_add]
        else:
            to_add.append(Organisation.objects.get(id=UUID(org_uuid)))

        added_users_results = [
            self.organisation_get_create_user(organisation=organisation, exporter_user=exporter_user)
            for organisation in to_add
        ]

        added_users_count = sum([1 for _, created in added_users_results if created])
        print(f"Added {exporter_user.email} to {added_users_count} organisations")
        return

    def remove(self, org_uuid, exporter_user):
        if org_uuid == "all":
            count, _ = self.organisation_delete_user_from_all(exporter_user=exporter_user)
        else:
            organisation = Organisation.objects.get(id=UUID(org_uuid))
            count, _ = self.organisation_delete_user(organisation=organisation, exporter_user=exporter_user)

        print(f"Removed {exporter_user.email} from {count} organisations")
        return


class ActionSiel(ActionBase):
    def action(self, options):
        print("Add SIEL applications to organisations")
        app_count_min, app_count_max = self.get_min_max_arg(options)
        goods_count_max = self.get_arg(options, "max_goods", 1)
        org_count = self.get_arg(options, "count", 1)
        uuid = self.get_arg(options, "uuid", required=False)
        mt = self.get_arg(options, "mt", required=False)
        organisations = [Organisation.objects.get(id=UUID(uuid))] if uuid else self.organisation_get_first_n(org_count)

        # figure out the correct number of standard applications to add to each organisation
        org_app_counts = [
            (
                org,
                StandardApplication.objects.filter(organisation_id=org.id).count(),
                random.randint(app_count_min, app_count_max),
            )
            for org in organisations
        ]
        applications_to_add_per_org = [
            (org, required_app_count - current_app_count)
            for org, current_app_count, required_app_count in org_app_counts
            if current_app_count < required_app_count
        ]

        job_args = [
            (ActionBase.app_factory, org, apps_to_add, goods_count_max)
            for org, apps_to_add in applications_to_add_per_org
        ]

        apps = [application for application in self.get_mapper(mt)(ActionBase.do_work, job_args)]

        print(
            f"ensured between {app_count_min} and {app_count_max} applications for {org_count} organisations"
            f", added {sum(apps)} applications in total"
        )
        return apps


class ActionStats(ActionBase):
    def action(self, options):
        print(
            f"Organisations:{Organisation.objects.all().count()}"
            f"\nSIEL applications:{StandardApplication.objects.all().count()}"
            f"\nOrganisation Products:{Good.objects.all().count()}"
            f"\nProducts used in SEIL applications:{GoodOnApplication.objects.all().count()}"
            f"\nExport Users:{ExporterUser.objects.all().count()}"
            f"\nFlags:{Flag.objects.all().count()}"
        )


class ActionSites(ActionBase):
    def action(self, options):
        print("Add sites to organisations")

        min_items, max_items = self.get_min_max_arg(options)
        org_count = self.get_arg(options, "count", 1)
        uuid = self.get_arg(options, "uuid", required=False)
        organisations = [Organisation.objects.get(id=UUID(uuid))] if uuid else self.organisation_get_first_n(org_count)

        site_results = [
            self.organisation_get_create_sites(organisation, random.randint(min_items, max_items))
            for organisation in organisations
        ]
        added_counts = [count for sites, count in site_results]

        print(f"ensured between {min_items} and {max_items} sites for {org_count} organisations")
        print(f"added {sum(added_counts)} site in total")


class ActionGoods(ActionBase):
    def action(self, options):
        print("Add goods to organisations")
        min_goods, max_goods = self.get_min_max_arg(options)
        org_count = self.get_arg(options, "count", 1)
        uuid = self.get_arg(options, "uuid", required=False)
        mt = self.get_arg(options, "mt", required=False)
        organisations = [Organisation.objects.get(id=UUID(uuid))] if uuid else self.organisation_get_first_n(org_count)
        job_args = [
            (ActionBase.organisation_get_create_goods, organisation, random.randint(min_goods, max_goods))
            for organisation in organisations
        ]
        added_goods = [len(goods_added) for _, goods_added in self.get_mapper(mt)(ActionBase.do_work, job_args)]

        print(f"ensured between {min_goods} and {max_goods} goods for {org_count} organisations")
        print(f"added {sum(added_goods)} goods in total")


class Command(SeedCommand):
    help = "Seeds data"
    info = "Seeding data"
    success = "Successfully completed action"
    seed_command = "seeddata"
    action_map = {
        "org": ActionOrg(),
        "fakeuser": ActionAddFakeUsers(),
        "user": ActionUser(),
        "siel": ActionSiel(),
        "site": ActionSites(),
        "stats": ActionStats(),
        "good": ActionGoods(),
        "eua": ActionEndUserAdvisory(),
    }

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument("-a", "--action", help="action command", choices=list(self.action_map.keys()), type=str)
        parser.add_argument("--uuid", help="a uuid", type=str)
        parser.add_argument("--mt", help="run multi-threaded, provide the number of threads to use", type=int)
        parser.add_argument("-c", "--count", help="item count", type=int)
        parser.add_argument("--max", help="max number of items", type=int)
        parser.add_argument("--min", help="min number of items", type=int)
        parser.add_argument("-e", "--email", help="user email", type=str)
        parser.add_argument("--type", help="a type", type=str)
        parser.add_argument("--max-goods", help="max number of goods", type=int)
        parser.add_argument("-r", "--remove", action="store_true", help="remove an item or items")

    def operation(self, *args, **options):
        action = options.get("action")
        if not action:
            raise Exception("action not specified!")
        self.stdout.write(self.style.SUCCESS(f"action = {action}"))
        tic = perf_counter()

        self.action_map[action].action(options)
        toc = perf_counter()
        print(f"action completed in {toc - tic:0.4f} seconds")
