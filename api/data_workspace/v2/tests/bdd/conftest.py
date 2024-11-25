import datetime
import json
import pytest
import pytz

from rest_framework import status
from rest_framework.test import APIClient

from pytest_bdd import (
    parsers,
    then,
)

from django.urls import reverse

from api.applications.tests.factories import (
    GoodOnApplicationFactory,
    PartyOnApplicationFactory,
    StandardApplicationFactory,
    DraftStandardApplicationFactory,
)
from api.cases.enums import CaseTypeEnum
from api.cases.models import CaseType
from api.core.constants import (
    ExporterPermissions,
    GovPermissions,
    Roles,
)
from api.goods.tests.factories import GoodFactory
from api.letter_templates.models import LetterTemplate
from api.organisations.tests.factories import OrganisationFactory
from api.staticdata.letter_layouts.models import LetterLayout
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.units.enums import Units
from api.users.libraries.user_to_token import user_to_token
from api.users.enums import SystemUser, UserType
from api.users.models import BaseUser, Permission
from api.users.tests.factories import (
    BaseUserFactory,
    ExporterUserFactory,
    GovUserFactory,
    RoleFactory,
    UserOrganisationRelationshipFactory,
)


def load_json(filename):
    with open(filename) as f:
        return json.load(f)


@pytest.fixture()
def seed_layouts():
    layouts = load_json("api/data_workspace/v2/tests/bdd/initial_data/letter_layouts.json")
    for layout in layouts:
        LetterLayout.objects.get_or_create(**layout)


@pytest.fixture()
def seed_templates(seed_layouts):
    # if this template exists the seed command is executed and all templates are seeded
    if LetterTemplate.objects.filter(name="SIEL template").exists():
        return

    templates = load_json("api/data_workspace/v2/tests/bdd/initial_data/letter_templates.json")
    for template in templates:
        template_instance, _ = LetterTemplate.objects.get_or_create(**template)
        template_instance.case_types.add(CaseType.objects.get(id=CaseTypeEnum.SIEL.id))


@pytest.fixture()
def siel_template(seed_templates):
    return LetterTemplate.objects.get(layout_id="00000000-0000-0000-0000-000000000001")


@pytest.fixture()
def siel_refusal_template(seed_templates):
    return LetterTemplate.objects.get(layout_id="00000000-0000-0000-0000-000000000006")


@pytest.fixture(autouse=True)
def system_user(db):
    if BaseUser.objects.filter(id=SystemUser.id).exists():
        return BaseUser.objects.get(id=SystemUser.id)
    else:
        return BaseUserFactory(id=SystemUser.id)


@pytest.fixture()
def gov_user():
    return GovUserFactory()


@pytest.fixture()
def lu_user():
    return GovUserFactory()


@pytest.fixture()
def gov_user_permissions():
    for permission in GovPermissions:
        Permission.objects.get_or_create(id=permission.name, name=permission.value, type=UserType.INTERNAL.value)


@pytest.fixture()
def lu_case_officer(gov_user, gov_user_permissions):
    gov_user.role = RoleFactory(name="Case officer", type=UserType.INTERNAL)
    gov_user.role.permissions.set(
        [
            GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
            GovPermissions.MANAGE_LICENCE_DURATION.name,
            GovPermissions.REOPEN_CLOSED_CASES.name,
        ]
    )
    gov_user.save()
    return gov_user


@pytest.fixture()
def lu_case_officer_headers(lu_case_officer):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(lu_case_officer.baseuser_ptr)}


@pytest.fixture()
def lu_senior_manager(lu_user, gov_user_permissions):
    lu_user.role = RoleFactory(
        id=Roles.INTERNAL_LU_SENIOR_MANAGER_ROLE_ID, name="LU Senior Manager", type=UserType.INTERNAL
    )
    lu_user.role.permissions.set(
        [GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name, GovPermissions.MANAGE_LICENCE_DURATION.name]
    )
    lu_user.save()
    return lu_user


@pytest.fixture()
def gov_headers(gov_user):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}


@pytest.fixture()
def lu_case_officer_headers(lu_case_officer):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(lu_case_officer.baseuser_ptr)}


@pytest.fixture()
def lu_sr_manager_headers(lu_senior_manager):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(lu_senior_manager.baseuser_ptr)}


@pytest.fixture()
def exporter_user():
    return ExporterUserFactory()


@pytest.fixture()
def exporter_user_permissions():
    for permission in ExporterPermissions:
        Permission.objects.get_or_create(id=permission.name, name=permission.value, type=UserType.EXPORTER.value)


@pytest.fixture()
def organisation(exporter_user_permissions, exporter_user):
    organisation = OrganisationFactory()

    UserOrganisationRelationshipFactory(
        organisation=organisation,
        role__permissions=[ExporterPermissions.SUBMIT_LICENCE_APPLICATION.name],
        user=exporter_user,
    )

    return organisation


@pytest.fixture()
def exporter_headers(exporter_user, organisation):
    return {
        "HTTP_EXPORTER_USER_TOKEN": user_to_token(exporter_user.baseuser_ptr),
        "HTTP_ORGANISATION_ID": str(organisation.id),
    }


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture()
def unpage_data(client):
    def _unpage_data(url):
        unpaged_results = []
        while True:
            response = client.get(url)
            assert response.status_code == status.HTTP_200_OK
            unpaged_results += response.data["results"]
            if not response.data["next"]:
                break
            url = response.data["next"]

        return unpaged_results

    return _unpage_data


@pytest.fixture()
def standard_application():
    application = StandardApplicationFactory(
        status=CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW),
    )
    party_on_application = PartyOnApplicationFactory(application=application)
    good = GoodFactory(organisation=application.organisation)
    good_on_application = GoodOnApplicationFactory(
        application=application, good=good, quantity=100.0, value=1500, unit=Units.NAR
    )
    return application


@pytest.fixture()
def draft_application():
    draft_application = DraftStandardApplicationFactory()
    return draft_application


@then(parsers.parse("the `{table_name}` table is empty"))
def empty_table(client, unpage_data, table_name):
    metadata_url = reverse("data_workspace:v2:table-metadata")
    response = client.get(metadata_url)
    tables_metadata = response.json()["tables"]
    for m in tables_metadata:
        if m["table_name"] == table_name:
            table_metadata = m
            break
    else:
        pytest.fail(f"No table called {table_name} found")

    table_data = unpage_data(table_metadata["endpoint"])

    assert table_data == [], f"`{table_name}` table should be empty"


@pytest.fixture()
def parse_table():
    def _parse_table(data_table):
        lines = data_table.strip().split("\n")
        rows = []
        for line in lines:
            values = [value.strip() for value in line.split("|") if value]
            rows.append(values)
        return rows

    return _parse_table


def cast_to_types(data, fields_metadata):
    fields_metadata = {field["name"]: field for field in fields_metadata}

    cast_data = []
    for row in data:
        cast_row = row.copy()
        for key, value in cast_row.items():
            field_metadata = fields_metadata[key]
            if value == "NULL":
                cast_row[key] = None
            elif field_metadata["type"] == "Integer":
                cast_row[key] = int(value)
            elif field_metadata["type"] == "DateTime":
                cast_row[key] = pytz.utc.localize(datetime.datetime.fromisoformat(value))
        cast_data.append(cast_row)

    return cast_data


@then(parsers.parse("the `{table_name}` table has the following rows:{rows}"))
def check_rows(client, parse_table, unpage_data, table_name, rows):
    metadata_url = reverse("data_workspace:v2:table-metadata")
    response = client.get(metadata_url)
    tables_metadata = response.json()["tables"]
    for m in tables_metadata:
        if m["table_name"] == table_name:
            table_metadata = m
            break
    else:
        pytest.fail(f"No table called {table_name} found")

    actual_data = unpage_data(table_metadata["endpoint"])
    parsed_rows = parse_table(rows)
    keys = parsed_rows[0]
    expected_data = []
    for row in parsed_rows[1:]:
        expected_data.append({key: value for key, value in zip(keys, row)})
    expected_data = cast_to_types(expected_data, table_metadata["fields"])
    assert actual_data == expected_data
