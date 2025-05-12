import pytest

from freezegun import freeze_time
from itertools import product
from urllib import parse

from django.urls import reverse
from rest_framework import status

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.core.constants import GovPermissions
from api.picklists.enums import PicklistType, PickListStatus
from api.picklists.models import PicklistItem
from api.picklists.tests.factories import PicklistItemFactory
from api.teams.models import Team
from api.users.libraries.user_to_token import user_to_token

from test_helpers.clients import DataTestClient

from lite_routing.routing_rules_internal.enums import TeamIdEnum

pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


@pytest.fixture(scope="function")
def setup(
    hawk_authentication,
):
    return


@pytest.fixture
def hawk_authentication(settings):
    settings.HAWK_AUTHENTICATION_ENABLED = True


@pytest.fixture
def url():
    return reverse("picklist_items:picklist_items")


class TestPicklistItemsView:

    @pytest.mark.parametrize(
        "team_id, item_types",
        (
            (
                TeamIdEnum.FCDO,
                [PicklistType.F680_PROVISO, PicklistType.STANDARD_ADVICE],
            ),
            (
                TeamIdEnum.MOD_CAPPROT,
                [PicklistType.PROVISO, PicklistType.STANDARD_ADVICE, PicklistType.REFUSAL_REASON],
            ),
            (
                TeamIdEnum.MOD_DI,
                [PicklistType.ECJU, PicklistType.F680_PROVISO],
            ),
            (
                TeamIdEnum.MOD_DSR,
                [PicklistType.FOOTNOTES],
            ),
            (
                TeamIdEnum.MOD_DSTL,
                [PicklistType.LETTER_PARAGRAPH],
            ),
            (
                TeamIdEnum.NCSC,
                [PicklistType.PROVISO, PicklistType.F680_PROVISO, PicklistType.REPORT_SUMMARY],
            ),
        ),
    )
    def test_ogds_retrieve_picklist_items(self, get_hawk_client, team_case_advisor_headers, team_id, item_types):
        team = Team.objects.get(id=team_id)

        for item_type in item_types:
            PicklistItemFactory(team_id=team_id, name=f"{team.name}", type=item_type)

        headers = team_case_advisor_headers(team_id)

        for item_type in item_types:
            query_params = {"name": team.name, "type": item_type}
            url = f'{reverse("picklist_items:picklist_items")}?{parse.urlencode(query_params, doseq=True)}'
            api_client, target_url = get_hawk_client("GET", url)
            response = api_client.get(target_url, **headers)
            assert response.status_code == status.HTTP_200_OK
            response = response.json()
            assert response["count"] == 1
            assert PicklistItem.objects.filter(name=team.name, type=item_type).count() == 1

            actual = [{"name": item["name"], "type": item["type"]["key"]} for item in response["results"]]
            expected = [{"name": team.name, "type": item_type}]
            assert actual == expected

    @freeze_time("2025-01-01 12:00:01")
    @pytest.mark.parametrize(
        "team_id, picklist_type",
        list(
            product(
                [
                    TeamIdEnum.FCDO,
                    TeamIdEnum.MOD_CAPPROT,
                    TeamIdEnum.MOD_DI,
                    TeamIdEnum.MOD_DSR,
                    TeamIdEnum.MOD_DSTL,
                    TeamIdEnum.NCSC,
                ],
                dict(PicklistType.choices).keys(),
            )
        ),
    )
    def test_ogds_create_picklist_items(
        self, gov_user_permissions, get_hawk_client, team_case_advisor, url, team_id, picklist_type
    ):
        team = Team.objects.get(id=team_id)
        data = {
            "name": f"{team.name} provisos",
            "text": f"{team.name}: provisos detailed text",
            "type": picklist_type,
            "team": team_id,
            "status": PickListStatus.ACTIVE,
        }
        gov_user = team_case_advisor(team_id, [GovPermissions.MANAGE_PICKLISTS.name])
        headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
        api_client, target_url = get_hawk_client("POST", url, data=data)
        response = api_client.post(target_url, data, **headers)
        assert response.status_code == status.HTTP_201_CREATED

        picklist_types_dict = dict(PicklistType.choices)

        actual = response.json()["picklist_item"]
        obj = PicklistItem.objects.get(id=actual["id"])
        assert actual == {
            "id": str(obj.id),
            **data,
            "type": {"key": picklist_type, "value": picklist_types_dict[picklist_type]},
            "status": {"key": "active", "value": "Active"},
            "team_name": team.name,
            "updated_at": "2025-01-01T12:00:01Z",
        }

        audit_event = Audit.objects.get(verb=AuditType.CREATED_PICKLIST, target_object_id=obj.id)
        assert audit_event.actor == gov_user


class PicklistsViews(DataTestClient):
    url = reverse("picklist_items:picklist_items")

    def setUp(self):
        super().setUp()
        other_team = self.create_team("Team")
        self.picklist_item_1 = self.create_picklist_item("#1", self.team, PicklistType.PROVISO, PickListStatus.ACTIVE)
        self.picklist_item_2 = self.create_picklist_item("#2", self.team, PicklistType.PROVISO, PickListStatus.ACTIVE)
        self.create_picklist_item("#3", self.team, PicklistType.REPORT_SUMMARY, PickListStatus.ACTIVE)
        self.create_picklist_item("#4", self.team, PicklistType.REPORT_SUMMARY, PickListStatus.DEACTIVATED)
        self.create_picklist_item("#5", other_team, PicklistType.ECJU, PickListStatus.ACTIVE)

    def test_gov_user_can_see_all_their_teams_picklist_items(self):
        response = self.client.get(self.url + "?show_deactivated=True", **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 4)

    def test_gov_user_can_see_all_their_teams_picklist_items_excluding_deactivated(
        self,
    ):
        response = self.client.get(self.url + "?show_deactivated=False", **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 3)

    def test_gov_user_can_see_all_their_teams_picklist_items_filter_by_name(
        self,
    ):
        response = self.client.get(self.url + "?name=3", **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 1)

    def test_gov_user_can_see_filtered_picklist_items(self):
        response = self.client.get(
            self.url + "?type=" + PicklistType.REPORT_SUMMARY + "?show_deactivated=True", **self.gov_headers
        )
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 1)

    def test_gov_user_can_see_filtered_picklist_items_excluding_deactivated(self):
        response = self.client.get(self.url + "?type=" + PicklistType.REPORT_SUMMARY, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 1)

    def test_gov_user_can_see_items_by_ids_filter(self):
        response = self.client.get(
            self.url
            + "?type="
            + PicklistType.PROVISO
            + "&ids="
            + str(self.picklist_item_1.id)
            + ","
            + str(self.picklist_item_2.id),
            **self.gov_headers,
        )
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 2)


class PicklistView(DataTestClient):
    def setUp(self):
        super().setUp()
        self.picklist = self.create_picklist_item("#1", self.team, PicklistType.PROVISO, PickListStatus.ACTIVE)
        self.url = reverse("picklist_items:picklist_item", kwargs={"pk": self.picklist.id})

    def test_gov_user_can_view_a_picklist_item(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_PICKLISTS.name])

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["picklist_item"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.picklist.id))
        self.assertEqual(response_data["name"], self.picklist.name)
        self.assertEqual(response_data["text"], self.picklist.text)
        self.assertEqual(response_data["team"]["id"], str(self.team.id))
        self.assertEqual(response_data["team"]["name"], self.team.name)
        self.assertEqual(response_data["type"]["key"], self.picklist.type)
        self.assertEqual(response_data["status"]["key"], self.picklist.status)
