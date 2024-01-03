import random

from decimal import Decimal
from faker import Faker

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.applications.models import StandardApplication
from api.applications.tests.factories import (
    GoodFactory,
    GoodOnApplicationFactory,
    PartyFactory,
    PartyOnApplicationFactory,
    StandardApplicationFactory,
)
from api.cases.models import Case
from api.goods.models import Good
from api.organisations.models import Organisation
from api.organisations.tests.factories import OrganisationFactory
from api.parties.enums import PartyType
from api.parties.models import Party
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.countries.factories import CountryFactory
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from api.teams.tests.factories import TeamFactory
from api.users.models import BaseUser, GovUser
from api.users.tests.factories import GovUserFactory

from lite_routing.routing_rules_internal.constants import RED_DESTINATION_MAP, GREEN_COUNTRIES_MAP, GREY_COUNTRIES_MAP


MAX_NUMBER_OF_ORGANISATIONS = 5
NUMBER_OF_PRODUCTS_IN_CATALOGUE = 300

faker = Faker()

# pool of Product names used when creating product catalogue
product_names = [
    "Rifle",
    "Shotgun",
    "Over and under shotgun",
    "Thermal scope",
    "User manuals",
    "Suppressor",
    "tactical suppressor",
    "Magazine assembly",
    "firing pin",
    "Barrel",
    "Cleaning kit",
    "Remote control unit",
    "Catridge assembly",
    "Proximity sensor",
    "Sling",
    "Battery cap",
    "7mm round",
    "9mm round",
    "Scope",
    "Thermal imaging camera",
    "joystick",
    "Accelerator",
    "gauge shotgun catridges",
    "Rail assembly",
    "Technology",
    "9mm Ammunition",
    "wave guide",
    "Sulphuric acid",
    "Hydrogen Fluoride",
    "Motor assembly",
    "Bolt action rifle",
    "Ammonium hydrogen",
    "piston",
    "Imaging Camera",
    "Sodium Chloride",
    "Di-Hydrogen Oxide",
    "military helmet",
    "Range finder",
    "Coaxial cable",
    "Multi-axis magnetic field sensor",
    "Image sensor",
    "Thermal sensor",
    "Brakes",
    "Technical publication",
    "Binoculars",
    "IR camera",
    "Bearing",
    "Technology transfer",
    "Pressure transducer",
    "Monopod",
    "Trigger cable",
    "Hydrofluoric acid",
    "Thermal IP camera",
    "sensor1",
    "sensor2",
    "sensor3",
    "sensor4",
    "sensor5",
    ".308 Magazine",
    ".18 Magazine",
    "HCL 10ml",
    "H2SO4 200ml",
    "10ml silica gel",
    "products using plastic",
    "sunshades for telescope",
    "Feet for tripod",
    "polarizing filter",
    "low pass filter",
    "high pass filter",
    "brush nylon",
    "mounting sleeve",
]

# Assumes prefix is assigned 20% of the time
rs_prefix_randomize = [True, False, False, False, False]

ALL_COUNTRIES = {**GREEN_COUNTRIES_MAP, **GREY_COUNTRIES_MAP}


class Command(BaseCommand):
    organisations = []
    products = []

    def add_arguments(self, parser):
        parser.add_argument(
            "count",
            type=int,
            help="Number of applications to be created",
        )

    def clean_up(self):
        # unassign all Cases from all queues
        for c in Case.objects.all():
            if c.queues.count():
                c.queues.clear()

        for organisation in Organisation.objects.all():
            Good.objects.filter(organisation=organisation).delete()

        StandardApplication.objects.all().delete()
        Party.objects.all().delete()

    def create_test_organisations(self):
        for i in range(MAX_NUMBER_OF_ORGANISATIONS):
            self.organisations.append(OrganisationFactory())

    def create_product_catalogue(self):
        # Create certain number of products for this organisation which
        # will be used in various applications
        for i in range(NUMBER_OF_PRODUCTS_IN_CATALOGUE):
            organisation = random.choice(self.organisations)
            random.shuffle(product_names)
            name = random.choice(product_names)
            self.products.append(GoodFactory(name=name, organisation=organisation))

    def handle(self, *args, **options):
        user = {
            "first_name": "TAU",
            "last_name": "User",
            "email": "tautest@example.com",
        }
        num_applications = options.pop("count")

        control_list_entries = list(ControlListEntry.objects.all())
        regime_entries = list(RegimeEntry.objects.all())
        rs_prefixes = list(ReportSummaryPrefix.objects.all())
        rs_subjects = list(ReportSummarySubject.objects.all())

        self.clean_up()

        team = TeamFactory()
        base_user = None
        gov_user = None
        if BaseUser.objects.filter(**user).exists():
            base_user = BaseUser.objects.filter(**user).first()
            gov_user = GovUser.objects.get(baseuser_ptr=base_user)
        else:
            gov_user = GovUserFactory(baseuser_ptr=base_user, team=team)

        self.create_test_organisations()
        self.create_product_catalogue()

        for _ in range(num_applications):
            application = StandardApplicationFactory()
            case = Case.objects.get(id=application.id)
            case.submitted_at = timezone.now()
            case.save()
            num_products = faker.random_number(1)
            for _ in range(num_products):
                cle = random.choice(control_list_entries)
                regime_entry = random.choice(regime_entries)
                prefix = random.choice(rs_prefixes)
                subject = random.choice(rs_subjects)
                add_prefix = random.choice(rs_prefix_randomize)
                report_summary = subject.name
                if add_prefix:
                    report_summary = f"{prefix.name} {subject.name}"

                good = random.choice(self.products)
                good_on_application = GoodOnApplicationFactory(
                    application=application,
                    good=good,
                    quantity=faker.random_number(2),
                    unit="NAR",
                    value=Decimal(faker.random_number(3)),
                    report_summary_prefix=prefix if add_prefix else None,
                    report_summary_subject=subject,
                    report_summary=report_summary,
                    assessed_by=gov_user,
                    comment=f"{faker.sentence()} {good.name}",
                )
                good.control_list_entries.set([cle])
                good_on_application.control_list_entries.set([cle])
                good_on_application.regime_entries.set([regime_entry])

            # All applications are going to have three parties
            for party_type in [PartyType.CONSIGNEE, PartyType.END_USER, PartyType.ULTIMATE_END_USER]:
                country_id, country_name = random.choice(list(RED_DESTINATION_MAP.items()))
                country_data = {"id": country_id, "name": country_name}
                country = CountryFactory(**country_data)
                PartyOnApplicationFactory(
                    application=application,
                    party=PartyFactory(**{"name": faker.company(), "type": party_type}, country=country),
                )
