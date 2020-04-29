import random

from django.db import transaction

from applications.managers import BaseApplicationManager
from applications.models import StandardApplication
from organisations.enums import OrganisationType
from organisations.models import Organisation
from organisations.tests.providers import OrganisationProvider
from faker import Faker
from static.management.SeedCommand import SeedCommand
from static.management.commands.seedapplication import Command as AppCommand
from static.management.commands.seedorganisation import Command as OrgCommand

faker = Faker()
faker.add_provider(OrganisationProvider)


class Params(object):
    pass


@transaction.atomic
class Command(SeedCommand):
    """
    pipenv run ./manage.py seeddata>
    """

    help = "Seeds data"
    info = "Seeding data"
    success = "Successfully seeded data"
    seed_command = "seeddata"

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument("--org-count", help="the number of organisations", type=int)
        parser.add_argument("--org-site-max", help="max number of sites", type=int)
        parser.add_argument("--org-site-min", help="min number of sites", type=int)
        parser.add_argument("--org-user-min", help="number of users", type=int)
        parser.add_argument("--org-user-max", help="number of users", type=int)
        parser.add_argument("--org-primary", help="primary email", type=str)
        parser.add_argument("--org-goods", help="number of goods", type=int)
        parser.add_argument("--org-applications", help="number of goods", type=int)

    @staticmethod
    def org_factory(params):
        org_name = faker.company()
        if Organisation.objects.filter(name__iexact=org_name).exists():
            idx = 1
            new_name = f"{org_name} ({idx})"
            while Organisation.objects.filter(name__iexact=new_name).exists():
                idx += 1
                new_name = f"{org_name} ({idx})"
            org_name = new_name

        result = OrgCommand.seed_organisation(
            org_name,
            OrganisationType.COMMERCIAL,
            random.randint(
                params.org_site_min,
                params.org_site_max),
            random.randint(
                params.org_user_min,
                params.org_user_max),
            params.org_primary)
        return result[0]

    @staticmethod
    def app_factory(org, applications_to_add, max_goods_to_use):
        organisation, submitted_applications, goods_added_to_org = AppCommand.seed_siel_applications(
            org,
            applications_to_add,
            max_goods_to_use,
        )
        return len(submitted_applications)

    @transaction.atomic
    def operation(self, *args, **options):
        params = Params()
        params.org_count = options.get("org_count") or 1
        params.org_site_max = options.get("org_site_max") or 1
        params.org_site_min = options.get("org_site_min") or 1
        params.org_user_min = options.get("org_user_min") or 1
        params.org_user_max = options.get("org_user_max") or 1
        params.org_primary = options.get("org_primary")
        params.org_goods = options.get("org_goods") or 1
        params.org_applications = options.get("org_applications") or 0

        print(f"org-count={params.org_count}")
        print(f"org_site_max={params.org_site_max}")
        print(f"org_site_min={params.org_site_min}")
        print(f"org_user_min={params.org_user_min}")
        print(f"org_user_max={params.org_user_max}")
        print(f"org_site_primary={params.org_primary}")
        print(f"org_goods={params.org_goods}")
        print(f"org_applications={params.org_applications}")

        # ensure the correct number of organisations
        orgs = list(Organisation.objects.all()[:params.org_count])
        required = max(0, params.org_count - len(orgs))
        orgs += [self.org_factory(params) for _ in range(0, required)]
        print(f"identified {params.org_count} organisations to use")

        # ensure the correct number of standard applications per org
        org_app_counts = [(org, StandardApplication.objects.filter(organisation_id=org.id).count())
                          for org in orgs]
        applications_to_add = [(org, params.org_applications - count)
                               for org, count in org_app_counts if count < params.org_applications]
        apps = [self.app_factory(
            org=org,
            max_goods_to_use=params.org_goods,
            applications_to_add=apps_to_add)
            for org, apps_to_add in applications_to_add]

        print(f"ensured  {params.org_applications} applications for the first {params.org_count} organisations"
              f", adding {sum(apps)} applications")
