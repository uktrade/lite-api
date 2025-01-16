import pytest

from django.urls import reverse
from urllib import parse

from api.applications.models import StandardApplication
from api.applications.tests.factories import DraftStandardApplicationFactory
from api.cases.models import Case
from api.flags.enums import FlagLevels
from api.queues.constants import ALL_CASES_QUEUE_ID

from lite_routing.routing_rules_internal.enums import FlagsEnum

pytestmark = pytest.mark.django_db


@pytest.fixture
def all_cases_queue_url():
    query_params = {"queue_id": ALL_CASES_QUEUE_ID}
    return f"{reverse('cases:search')}?{parse.urlencode(query_params, doseq=True)}"


@pytest.fixture
def standard_case(organisation, submit_application):
    draft = DraftStandardApplicationFactory(organisation=organisation)
    application = submit_application(draft)
    return Case.objects.get(id=application.id)


@pytest.fixture
def case_with_flags(standard_case):
    def _case_with_flags(flags_data):
        case_flags = flags_data.get(FlagLevels.CASE, [])
        standard_case.flags.add(*case_flags)

        application = StandardApplication.objects.get(id=standard_case.id)
        good_flags = flags_data.get(FlagLevels.GOOD, [])
        for good_on_application in application.goods.all():
            good_on_application.good.flags.add(*good_flags)

        destination_flags = flags_data.get(FlagLevels.DESTINATION, [])
        party_on_application_flags = flags_data.get(FlagLevels.PARTY_ON_APPLICATION, [])
        for party_on_application in application.parties.all():
            party_on_application.party.flags.add(*destination_flags)
            party_on_application.flags.add(*party_on_application_flags)

        return standard_case

    return _case_with_flags


@pytest.mark.parametrize(
    "flags_data",
    (
        {FlagLevels.CASE: [FlagsEnum.UNSCR_OFSI_SANCTIONS]},
        {FlagLevels.GOOD: [FlagsEnum.SMALL_ARMS, FlagsEnum.UK_DUAL_USE_SCH3]},
        {FlagLevels.DESTINATION: [FlagsEnum.OIL_AND_GAS_ID]},
        {FlagLevels.PARTY_ON_APPLICATION: [FlagsEnum.SANCTION_UK_MATCH, FlagsEnum.SANCTION_OFSI_MATCH]},
    ),
)
def test_queue_view_case_flags(
    api_client,
    all_cases_queue_url,
    case_with_flags,
    gov_headers,
    flags_data,
):
    case = case_with_flags(flags_data)

    response = api_client.get(all_cases_queue_url, **gov_headers)
    assert response.status_code == 200

    for case in response.json()["results"]["cases"]:
        all_flags = [
            item["id"] for flag_level in ["flags", "goods_flags", "destinations_flags"] for item in case[flag_level]
        ]

        for flags in flags_data.values():
            assert set(flags).issubset(set(all_flags))


@pytest.mark.parametrize(
    "flags_data",
    (
        {FlagLevels.CASE: [FlagsEnum.UNSCR_OFSI_SANCTIONS]},
        {FlagLevels.GOOD: [FlagsEnum.SMALL_ARMS, FlagsEnum.UK_DUAL_USE_SCH3]},
        {FlagLevels.DESTINATION: [FlagsEnum.OIL_AND_GAS_ID]},
        {FlagLevels.PARTY_ON_APPLICATION: [FlagsEnum.SANCTION_UK_MATCH, FlagsEnum.SANCTION_OFSI_MATCH]},
    ),
)
def test_case_detail_flags(
    api_client,
    case_with_flags,
    gov_headers,
    flags_data,
):
    case = case_with_flags(flags_data)

    url = reverse("cases:case", kwargs={"pk": case.id})
    response = api_client.get(url, **gov_headers)
    assert response.status_code == 200

    response = response.json()
    all_flags = [item["id"] for item in response["case"]["all_flags"]]

    for flags in flags_data.values():
        assert set(flags).issubset(set(all_flags))
