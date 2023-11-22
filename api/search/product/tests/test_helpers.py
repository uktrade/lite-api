from dateutil.parser import parse

from api.applications.models import StandardApplication
from api.applications.tests.factories import (
    GoodFactory,
    GoodOnApplicationFactory,
    PartyFactory,
    PartyOnApplicationFactory,
    StandardApplicationFactory,
)
from api.cases.models import CaseReferenceCode
from api.goods.models import Good
from api.organisations.models import Organisation
from api.organisations.tests.factories import OrganisationFactory
from api.parties.enums import PartyType
from api.parties.models import Party
from api.staticdata.countries.factories import CountryFactory
from api.teams.models import Team
from api.teams.tests.factories import TeamFactory
from api.users.models import GovUser
from api.users.tests.factories import BaseUserFactory, GovUserFactory

# Test data for applications
test_applications_data = [
    # Application 1
    {
        "application": {
            "name": "Export application for small arms",
        },
        "organisation": {"name": "Small arms org"},
        "products": [
            {
                "good": {
                    "name": "Bolt action sporting rifle",
                    "part_number": "ABC-123",
                    "is_good_controlled": True,
                    "control_list_entries": ["FR AI"],
                },
                "good_on_application": {
                    "is_good_controlled": True,
                    "report_summary": "sniper rifles",
                    "assessment_date": parse("2021-06-08T15:51:28.529110+00:00"),
                    "comment": "no concerns",
                    "quantity": 5,
                    "value": 1200.00,
                },
            },
            {
                "good": {
                    "name": "Thermal camera",
                    "part_number": "IMG-1300",
                    "is_good_controlled": True,
                    "control_list_entries": ["6A003"],
                },
                "good_on_application": {
                    "is_good_controlled": True,
                    "report_summary": "Imaging sensors",
                    "assessment_date": parse("2021-07-08T15:51:28.529110+00:00"),
                    "comment": "for industrial use only",
                    "quantity": 50,
                    "value": 1200.00,
                },
            },
            {
                "good": {
                    "name": "Magnetic field sensor",
                    "part_number": "TS1.5/M2",
                    "is_good_controlled": True,
                    "control_list_entries": ["6A006"],
                },
                "good_on_application": {
                    "is_good_controlled": True,
                    "report_summary": "Magnetic sensors",
                    "assessment_date": parse("2022-08-20T15:51:28.529110+00:00"),
                    "comment": "for industrial use only",
                    "quantity": 25,
                    "value": 5000.00,
                },
            },
        ],
        "parties": [
            {
                "name": "small arms org",
                "type": PartyType.CONSIGNEE,
                "country": {"id": "FR", "name": "France"},
            },
            {
                "name": "small industries",
                "type": PartyType.END_USER,
                "country": {"id": "FR", "name": "France"},
            },
        ],
        "case_advisor": {
            "first_name": "TAU",
            "last_name": "Advisor1",
        },
    },
    # Application 2
    {
        "application": {
            "name": "Export application for chemicals, components",
        },
        "organisation": {"name": "Spectral ltd"},
        "products": [
            {
                "good": {
                    "name": "Frequency shifter",
                    "part_number": "MS2X",
                    "is_good_controlled": True,
                    "control_list_entries": ["6A004"],
                },
                "good_on_application": {
                    "is_good_controlled": True,
                    "report_summary": "components for spectrometers",
                    "comment": "Research and development. Potentially under WVS regime",
                    "quantity": 100,
                    "value": 2500.34,
                },
            },
            {
                "good": {
                    "name": "Cherry MX Red",
                    "part_number": "MXR125H",
                    "is_good_controlled": True,
                    "control_list_entries": ["PL9010"],
                },
                "good_on_application": {
                    "is_good_controlled": True,
                    "report_summary": "mechanical keyboards",
                    "assessment_date": parse("2022-10-08T15:51:28.529110+00:00"),
                    "comment": "dual use",
                    "quantity": 60,
                    "value": 600.00,
                },
            },
            {
                "good": {
                    "name": "Sulphuric Acid",
                    "part_number": "H2SO4",
                    "is_good_controlled": True,
                    "control_list_entries": ["1D003"],
                },
                "good_on_application": {
                    "is_good_controlled": True,
                    "report_summary": "Chemicals",
                    "assessment_date": parse("2023-10-21T15:51:28.529110+00:00"),
                    "comment": "industrial use",
                    "quantity": 5,
                    "value": 100.00,
                },
            },
        ],
        "parties": [
            {
                "name": "app2_part1",
                "type": PartyType.CONSIGNEE,
                "country": {"id": "DE", "name": "Germany"},
            },
            {
                "name": "app2_party2",
                "type": PartyType.END_USER,
                "country": {"id": "AT", "name": "Austria"},
            },
        ],
        "case_advisor": {
            "first_name": "TAU",
            "last_name": "Advisor2",
        },
    },
    # Application 3
    {
        "application": {
            "name": "Export application for Optical equipment",
        },
        "organisation": {"name": "Optical equipment"},
        "products": [
            {
                "good": {
                    "name": "M3 Pro Max",
                    "part_number": "867-5309",
                    "is_good_controlled": True,
                    "control_list_entries": ["6A001a1d"],
                },
                "good_on_application": {
                    "is_good_controlled": True,
                    "report_summary": "marine position fixing equipment",
                    "regime_entries": ["Wassenaar Arrangement"],
                    "assessment_date": parse("2023-10-22T15:51:28.529110+00:00"),
                    "quantity": 15,
                    "value": 200.00,
                },
            },
            {
                "good": {
                    "name": "Instax HD camera",
                    "part_number": "abc123xyz",
                    "is_good_controlled": True,
                    "control_list_entries": ["6A003b4a"],
                },
                "good_on_application": {
                    "is_good_controlled": True,
                    "report_summary": "components for imaging cameras",
                    "regime_entries": ["Wassenaar Arrangement Sensitive"],
                    "assessment_date": parse("2023-10-23T15:51:28.529110+00:00"),
                    "quantity": 30,
                    "value": 2400.00,
                },
            },
            {
                "good": {
                    "name": "controlled chemical substance",
                    "part_number": "H2O2",
                    "is_good_controlled": True,
                    "control_list_entries": ["1C35016"],
                },
                "good_on_application": {
                    "is_good_controlled": True,
                    "report_summary": "chemicals used for general laboratory work/scientific research",
                    "regime_entries": ["CWC Schedule 3"],
                    "assessment_date": parse("2023-10-24T15:51:28.529110+00:00"),
                    "quantity": 45,
                    "value": 1200.00,
                },
            },
            {
                "good": {
                    "name": "Maintenance manual",
                    "part_number": "15606",
                    "is_good_controlled": False,
                    "control_list_entries": ["ML22a"],
                },
                "good_on_application": {
                    "is_good_controlled": False,
                    "report_summary": "technology for shotguns",
                    "assessment_date": parse("2023-08-24T15:51:28.529110+00:00"),
                    "quantity": 1000,
                    "value": 10000.00,
                },
            },
        ],
        "parties": [
            {
                "name": "app3_party1",
                "type": PartyType.CONSIGNEE,
                "country": {"id": "CA", "name": "Canada"},
            },
            {
                "name": "app3_party2",
                "type": PartyType.END_USER,
                "country": {"id": "GR", "name": "Greece"},
            },
            {
                "name": "app3_party3",
                "type": PartyType.ULTIMATE_END_USER,
                "country": {"id": "FI", "name": "Finland"},
            },
            {
                "name": "app3_party4",
                "type": PartyType.ULTIMATE_END_USER,
                "country": {"id": "PL", "name": "Poland"},
            },
        ],
        "case_advisor": {
            "first_name": "TAU",
            "last_name": "Advisor3",
        },
    },
]


def create_test_data():
    team = TeamFactory()
    for item in test_applications_data:
        application = StandardApplicationFactory(**item["application"])
        organisation = OrganisationFactory(**item["organisation"])
        for product_data in item["products"]:
            GoodOnApplicationFactory(
                application=application,
                good=GoodFactory(
                    **product_data["good"],
                    organisation=organisation,
                ),
                **product_data["good_on_application"],
                assessed_by=GovUserFactory(baseuser_ptr=BaseUserFactory(**item["case_advisor"]), team=team),
            )

        for party_data in item["parties"]:
            country = CountryFactory(**party_data.pop("country"))
            PartyOnApplicationFactory(
                application=application,
                party=PartyFactory(**party_data, country=country),
            )


def delete_test_data():
    for organisation in Organisation.objects.all():
        Good.objects.filter(organisation=organisation).delete()

    for team in Team.objects.all():
        GovUser.objects.filter(team=team).delete()

    StandardApplication.objects.all().delete()
    CaseReferenceCode.objects.all().delete()
    Party.objects.all().delete()
