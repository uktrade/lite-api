import random
import uuid

from api.applications.models import (
    BaseApplication,
    GoodOnApplication,
)
from api.goods.enums import GoodPvGraded, GoodControlled, GoodStatus
from api.goods.models import Good
from api.organisations.enums import OrganisationType
from api.organisations.models import Organisation
from api.staticdata.management.SeedCommand import SeedCommand
from api.staticdata.units.enums import Units
from test_helpers.clients import DataTestClient
from api.users.models import GovUser

# helper functions
def verify_good(good):
    good.status = GoodStatus.VERIFIED
    good.save()
    return good


def add_good(good, draft):
    quantity = random.randint(1, 10)
    value = random.randint(10, 10000) * quantity
    return GoodOnApplication.objects.create(
        good=good, application=draft, quantity=quantity, unit=Units.NAR, value=value
    )


def add_goods_to_application(goods_ids, draft):
    return [add_good(good, draft) for good in goods_ids]


def choose_some_goods(goods_ids, min_goods=1, max_goods=None):
    if not max_goods:
        max_goods = len(goods_ids)
    return random.sample(goods_ids, random.randint(1, max_goods))


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedapplications -count <number of applications> -goods <number of verified goods to choose from>
    """

    help = "Seeds applications for an individual or all organisations"
    info = "Seeding applications"
    success = "Successfully seeded applications"
    seed_command = "seedapplications"

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument("--org-id", help="Id of Organisation", type=str)
        parser.add_argument("--count", help="Number of applications to seed", type=int)
        parser.add_argument("--goods", help="Number of goods to seed", type=int)

    def operation(self, *args, **options):
        org_id = options.get("org_id") or None
        count = options.get("count") or 1
        goods = options.get("goods") or 1
        # Seed applications for Non-HMRC organisations
        organisations = (
            [Organisation.objects.exclude(type=OrganisationType.HMRC).get(id=org_id)]
            if org_id is not None
            else Organisation.objects.exclude(type=OrganisationType.HMRC)
        )
        [self.seed_siel_applications(org, count, goods) for org in organisations]

    @classmethod
    def seed_siel_applications(cls, organisation: Organisation, number_of_applications: int, number_of_goods: int):
        tc = DataTestClient()
        tc.exporter_user = random.choice(organisation.get_users())
        gov_user = GovUser.objects.first()

        # ensure all the required goods exist in the org product list, create if necessary
        goods, goods_added_to_org = cls.ensure_verified_goods_exist(number_of_goods, organisation, tc)

        # add draft applications to the
        drafts = [
            tc.create_draft_standard_application(
                organisation=organisation, reference_name="SIEL application", add_a_good=False
            )
            for _ in range(number_of_applications)
        ]

        [add_goods_to_application(choose_some_goods(goods, number_of_goods), draft) for draft in drafts]
        submitted_applications = [tc.submit_application(draft) for draft in drafts]

        [
            tc.create_case_document(user=gov_user, case=application, name=f"SIEL application.doc")
            for application in submitted_applications
        ]

        [cls._print_to_console(organisation, application) for application in submitted_applications]
        return organisation, submitted_applications, goods_added_to_org

    @classmethod
    def ensure_verified_goods_exist(cls, number_of_goods, organisation, tc=DataTestClient()):
        existing_goods = [good for good in Good.objects.filter(organisation_id=organisation.pk)]
        count_existing = len(existing_goods)
        expected_names = set(
            [f"{organisation.name} - Product {i + 1}" for i in range(max(count_existing, number_of_goods))]
        )
        existing_names = set([good.description for good in existing_goods])
        missing_names = expected_names - existing_names
        matched_names = existing_names - missing_names
        count_matched = len(matched_names)
        count_names_required = max(0, number_of_goods - count_matched)
        tc.export_user = random.choice(organisation.get_users())

        goods_added = [
            verify_good(
                tc.create_good(
                    description=name,
                    organisation=organisation,
                    is_good_controlled=random.choice([GoodControlled.YES, GoodControlled.NO, GoodControlled.UNSURE]),
                    control_list_entries=["ML1a"],
                    is_pv_graded=random.choice([GoodPvGraded.YES, GoodPvGraded.NO, GoodPvGraded.GRADING_REQUIRED]),
                )
            )
            for name in list(missing_names)[:count_names_required]
        ]

        [
            tc.create_good_document(
                organisation=organisation,
                good=good,
                name=f"{good.description}.doc",
                s3_key=str(uuid.uuid4()),
                user=tc.export_user,
            )
            for good in goods_added
        ]

        # select goods that match the expected good naming
        goods = [good for good in goods_added + existing_goods for name in expected_names if good.description == name]

        return goods, goods_added

    @classmethod
    def _print_to_console(cls, organisation: Organisation, application: BaseApplication):
        cls.print_created_or_updated(
            BaseApplication,
            {"org-id": str(organisation.id), "org-name": str(organisation.name), "application-id": str(application.id)},
            is_created=True,
        )
