import pytest

from rest_framework import status

from api.users.enums import SystemUser
from api.users.tests.factories import BaseUserFactory


@pytest.fixture(autouse=True)
def system_user(db):
    return BaseUserFactory(id=SystemUser.id)


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
