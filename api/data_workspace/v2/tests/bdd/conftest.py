import pytest

from rest_framework import status


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
