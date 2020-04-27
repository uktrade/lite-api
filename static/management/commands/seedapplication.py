import random

from django.db import transaction
from applications.models import (
    BaseApplication,
    GoodOnApplication,
)
from goods.enums import GoodPvGraded, GoodControlled, GoodStatus
from goods.models import Good
from organisations.models import Organisation
from static.management.SeedCommand import SeedCommand
from static.units.enums import Units
from test_helpers.clients import DataTestClient

# helper functions
def verify_good(good):
    good.status = GoodStatus.VERIFIED
    good.save()
    return good


def add_good(good, draft):
    quantity = random.randint(1, 10)
    value = random.randint(10, 10000) * quantity
    goa = GoodOnApplication(
        good=good,
        application=draft,
        quantity=quantity,
        unit=Units.NAR,
        value=value
    )
    goa.save()
    return goa


def add_goods_application(goods_ids, draft):
    return [add_good(good, draft) for good in goods_ids]


def choose_some_goods(goods_ids):
    return random.sample(goods_ids, random.randint(1, len(goods_ids)))


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedapplication -
    """

    help = "Seeds applications for an individual or all organisations"
    info = "Seeding applications"
    success = "Successfully seeded applications"
    seed_command = "seedapplication"

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument("--org-id", help="Id of Organisation", type=str)
        parser.add_argument("--count", help="Number of applications to seed", type=int)
        parser.add_argument("--goods", help="Number of goods to seed", type=int)

    @transaction.atomic
    def operation(self, *args, **options):
        org_id = options.get("org_id") or None
        count = options.get("count") or 1
        goods = options.get("goods") or 0
        organisations = [Organisation.objects.get(id=org_id)] if org_id is not None else Organisation.objects.all()
        [self.seed_applications(org, count, goods) for org in organisations]

    @classmethod
    def seed_applications(cls, organisation: Organisation, number_of_applications: int, number_of_goods: int):
        tc = DataTestClient()

        # add draft applications to the
        drafts = [tc.create_draft_standard_application(
            organisation=organisation,
            reference_name="SIEL application",
            add_a_good=False)
            for i in range(number_of_applications)]

        # ensure all the required goods exist in the org product list, create if necessary
        required_org_goods_names = [f"{organisation.name} - Product {i + 1}" for i in range(number_of_goods)]
        org_goods = [good for good in Good.objects.filter(organisation_id=organisation.pk)]
        names_of_goods_to_add = set(required_org_goods_names) - set([good.description for good in org_goods])
        goods_added_org = [verify_good(tc.create_good(
            description=name,
            org=organisation,
            is_good_controlled=random.choice([GoodControlled.YES, GoodControlled.NO, GoodControlled.UNSURE]),
            control_code="ML1a",
            is_pv_graded=random.choice([GoodPvGraded.YES, GoodPvGraded.NO, GoodPvGraded.GRADING_REQUIRED])))
            for name in names_of_goods_to_add]
        org_goods = goods_added_org + org_goods

        # find goods that could be added to the application
        all_goods = [good for good in org_goods for name in required_org_goods_names if good.description == name]

        [add_goods_application(choose_some_goods(all_goods), draft) for draft in drafts]
        submitted_applications = [tc.submit_application(draft) for draft in drafts]

        [cls._print_to_console(organisation, application) for application in submitted_applications]
        return organisation, submitted_applications

    @classmethod
    def _print_to_console(cls, organisation: Organisation, application: BaseApplication):
        cls.print_created_or_updated(
            BaseApplication,
            {
                "org-id": str(organisation.id),
                "org-name": str(organisation.name),
                "application-id": str(application.id)
            },
            is_created=True)
