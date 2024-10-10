import pytest

from rest_framework import status
from rest_framework.test import APIClient

from api.core.constants import (
    GovPermissions,
    Roles,
)
from api.organisations.tests.factories import OrganisationFactory
from api.users.enums import SystemUser
from api.users.libraries.user_to_token import user_to_token
from api.users.tests.factories import (
    BaseUserFactory,
    ExporterUserFactory,
    GovUserFactory,
    PermissionFactory,
    RoleFactory,
    UserOrganisationRelationshipFactory,
)


@pytest.fixture(autouse=True)
def system_user(db):
    return BaseUserFactory(id=SystemUser.id)


@pytest.fixture
def create_table():
    def _create_table(data_table):
        lines = data_table.strip().split("\n")

        keys = [key.strip() for key in lines[0].split("|") if key]

        parsed_data_table = []
        for line in lines[1:]:
            values = [value.strip() for value in line.split("|") if value]
            entry = dict(zip(keys, values))
            parsed_data_table.append(entry)

        return parsed_data_table

    return _create_table


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
def api_client():
    return APIClient()


@pytest.fixture()
def exporter_user():
    return ExporterUserFactory()


@pytest.fixture()
def organisation(exporter_user):
    organisation = OrganisationFactory()

    UserOrganisationRelationshipFactory(
        organisation=organisation,
        user=exporter_user,
    )

    return organisation


@pytest.fixture()
def exporter_headers(exporter_user, organisation):
    return {
        "HTTP_EXPORTER_USER_TOKEN": user_to_token(exporter_user.baseuser_ptr),
        "HTTP_ORGANISATION_ID": str(organisation.id),
    }


@pytest.fixture(autouse=True)
def internal_default_role_id(db):
    role = RoleFactory(
        pk=Roles.INTERNAL_DEFAULT_ROLE_ID,
        permissions=[
            PermissionFactory(pk=GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name),
        ],
    )
    return role


@pytest.fixture()
def gov_user():
    return GovUserFactory()


@pytest.fixture()
def gov_headers(gov_user):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
