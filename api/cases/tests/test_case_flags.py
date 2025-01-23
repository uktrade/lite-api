import pytest

from django.urls import reverse
from urllib import parse

from api.applications.tests.factories import StandardSubmittedApplicationFactory
from api.flags.enums import FlagLevels
from api.queues.constants import ALL_CASES_QUEUE_ID

from lite_routing.routing_rules_internal.enums import FlagsEnum

pytestmark = pytest.mark.django_db


@pytest.fixture
def all_cases_queue_url():
    query_params = {"queue_id": ALL_CASES_QUEUE_ID}
    return f"{reverse('cases:search')}?{parse.urlencode(query_params, doseq=True)}"


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
    gov_headers,
    mocker,
    flags_data,
):
    # When changes are saved in factory then post_save() signal can trigger flagging rules
    # and alter flags applied which is not desirable in these tests hence mock that function.
    mocker.patch("api.cases.signals.apply_flagging_rules_to_case", return_value=None)
    StandardSubmittedApplicationFactory(flags=flags_data)

    response = api_client.get(all_cases_queue_url, **gov_headers)
    assert response.status_code == 200

    for case in response.json()["results"]["cases"]:
        all_flags = [
            item["id"] for flag_level in ["flags", "goods_flags", "destinations_flags"] for item in case[flag_level]
        ]

        expected_flags = []
        for flags in flags_data.values():
            expected_flags.extend(flags)

        assert sorted(all_flags) == sorted(expected_flags)


@pytest.mark.parametrize(
    "flags_data",
    (
        {
            FlagLevels.CASE: [FlagsEnum.UNSCR_OFSI_SANCTIONS],
            FlagLevels.GOOD: [FlagsEnum.DUAL_USE_ANNEX_1],
        },
        {FlagLevels.GOOD: [FlagsEnum.SMALL_ARMS, FlagsEnum.UK_DUAL_USE_SCH3]},
        {FlagLevels.DESTINATION: [FlagsEnum.OIL_AND_GAS_ID]},
        {
            FlagLevels.CASE: [FlagsEnum.GOODS_NOT_LISTED],
            FlagLevels.PARTY_ON_APPLICATION: [FlagsEnum.SANCTION_UK_MATCH, FlagsEnum.SANCTION_OFSI_MATCH],
        },
    ),
)
def test_case_detail_flags(
    api_client,
    gov_headers,
    mocker,
    flags_data,
):
    mocker.patch("api.cases.signals.apply_flagging_rules_to_case", return_value=None)
    case = StandardSubmittedApplicationFactory(flags=flags_data)

    url = reverse("cases:case", kwargs={"pk": case.id})
    response = api_client.get(url, **gov_headers)
    assert response.status_code == 200

    response = response.json()
    all_flags = [item["id"] for item in response["case"]["all_flags"]]

    expected_flags = []
    for flags in flags_data.values():
        expected_flags.extend(flags)

    assert sorted(all_flags) == sorted(expected_flags)
