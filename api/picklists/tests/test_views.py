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

    @pytest.mark.parametrize(
        "query_params, query_filters, expected_count",
        (
            ({"show_deactivated": False}, [PickListStatus.ACTIVE], 2),
            ({"show_deactivated": True}, [PickListStatus.ACTIVE, PickListStatus.DEACTIVATED], 3),
        ),
    )
    def test_filter_by_status(
        self, get_hawk_client, team_case_advisor_headers, url, query_params, query_filters, expected_count
    ):
        PicklistItemFactory(team_id=TeamIdEnum.MOD_CAPPROT, type=PicklistType.PROVISO)
        PicklistItemFactory(team_id=TeamIdEnum.MOD_CAPPROT, type=PicklistType.F680_PROVISO)
        PicklistItemFactory(
            team_id=TeamIdEnum.MOD_CAPPROT, type=PicklistType.FOOTNOTES, status=PickListStatus.DEACTIVATED
        )
        PicklistItemFactory(team_id=TeamIdEnum.FCDO, type=PicklistType.STANDARD_ADVICE)

        url = f'{reverse("picklist_items:picklist_items")}?{parse.urlencode(query_params, doseq=True)}'
        api_client, target_url = get_hawk_client("GET", url)
        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        response = api_client.get(target_url, **headers)
        assert response.status_code == status.HTTP_200_OK
        response = response.json()
        assert response["count"] == expected_count
        actual = sorted(
            [
                {"team_id": item["team"]["id"], "type": item["type"]["key"], "status": item["status"]["key"]}
                for item in response["results"]
            ],
            key=lambda x: x["type"],
        )
        expected = [
            {"team_id": str(item.team_id), "type": item.type, "status": item.status}
            for item in PicklistItem.objects.filter(team_id=TeamIdEnum.MOD_CAPPROT, status__in=query_filters).order_by(
                "type"
            )
        ]
        assert actual == expected

    @pytest.mark.parametrize(
        "query_params, expected_count",
        (
            ({"type": PicklistType.STANDARD_ADVICE}, 1),
            ({"type": PicklistType.PROVISO}, 1),
            ({"type": PicklistType.F680_PROVISO}, 1),
            ({"type": PicklistType.REFUSAL_REASON}, 0),
        ),
    )
    def test_filter_by_type(self, get_hawk_client, team_case_advisor_headers, url, query_params, expected_count):
        PicklistItemFactory(team_id=TeamIdEnum.MOD_CAPPROT, type=PicklistType.PROVISO)
        PicklistItemFactory(team_id=TeamIdEnum.MOD_CAPPROT, type=PicklistType.F680_PROVISO)
        PicklistItemFactory(team_id=TeamIdEnum.MOD_CAPPROT, type=PicklistType.STANDARD_ADVICE)
        PicklistItemFactory(team_id=TeamIdEnum.FCDO, type=PicklistType.FOOTNOTES)

        url = f'{reverse("picklist_items:picklist_items")}?{parse.urlencode(query_params, doseq=True)}'
        api_client, target_url = get_hawk_client("GET", url)
        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        response = api_client.get(target_url, **headers)
        assert response.status_code == status.HTTP_200_OK
        response = response.json()
        assert response["count"] == expected_count
        actual = [
            {"team_id": item["team"]["id"], "type": item["type"]["key"], "status": item["status"]["key"]}
            for item in response["results"]
        ]
        expected = [
            {"team_id": str(item.team_id), "type": item.type, "status": item.status}
            for item in PicklistItem.objects.filter(team_id=TeamIdEnum.MOD_CAPPROT, type=query_params["type"])
        ]
        assert actual == expected

    @pytest.mark.parametrize(
        "query_params, expected_count",
        (
            ({"name": "FCDO"}, 3),
            ({"name": "FCDO 1"}, 1),
            ({"name": "FCDO 4"}, 0),
        ),
    )
    def test_filter_by_name(self, get_hawk_client, team_case_advisor_headers, url, query_params, expected_count):
        team = Team.objects.get(id=TeamIdEnum.FCDO)
        PicklistItemFactory(team_id=TeamIdEnum.FCDO, name=f"{team.name} 1")
        PicklistItemFactory(team_id=TeamIdEnum.FCDO, name=f"{team.name} 2")
        PicklistItemFactory(team_id=TeamIdEnum.FCDO, name=f"{team.name} 3")

        url = f'{reverse("picklist_items:picklist_items")}?{parse.urlencode(query_params, doseq=True)}'
        api_client, target_url = get_hawk_client("GET", url)
        headers = team_case_advisor_headers(TeamIdEnum.FCDO)
        response = api_client.get(target_url, **headers)
        assert response.status_code == status.HTTP_200_OK
        response = response.json()
        assert response["count"] == expected_count
        actual = [
            {"team_id": item["team"]["id"], "type": item["type"]["key"], "name": item["name"]}
            for item in response["results"]
        ]
        expected = [
            {"team_id": str(item.team_id), "type": item.type, "name": item.name}
            for item in PicklistItem.objects.filter(team_id=TeamIdEnum.FCDO, name__icontains=query_params["name"])
        ]
        assert actual == expected


class TestPicklistItemDetailView:

    @pytest.mark.parametrize(
        "team_id",
        (
            TeamIdEnum.FCDO,
            TeamIdEnum.MOD_CAPPROT,
            TeamIdEnum.MOD_DI,
            TeamIdEnum.MOD_DSR,
            TeamIdEnum.MOD_DSTL,
            TeamIdEnum.NCSC,
        ),
    )
    def test_ogds_view_picklist_item_details(
        self, gov_user_permissions, get_hawk_client, team_case_advisor_headers, team_id
    ):
        team = Team.objects.get(id=team_id)
        f680_proviso = PicklistItemFactory(team_id=team_id, name=f"{team.name}", type=PicklistType.F680_PROVISO)

        url = reverse("picklist_items:picklist_item", kwargs={"pk": f680_proviso.id})
        headers = team_case_advisor_headers(team_id)
        api_client, target_url = get_hawk_client("GET", url)
        response = api_client.get(target_url, **headers)
        assert response.status_code == status.HTTP_200_OK
        actual = response.json()["picklist_item"]
        assert actual["name"] == team.name
        assert actual["type"]["key"] == PicklistType.F680_PROVISO
        assert actual["team"]["id"] == team_id
        assert actual["status"]["key"] == PickListStatus.ACTIVE
