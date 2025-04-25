import pytest

from api.f680.tests.f680_test_data import AUSTRALIA_RELEASE_ID, FRANCE_RELEASE_ID, UAE_RELEASE_ID, APPLICATION_JSON


@pytest.fixture
def data_australia_release_id():
    return AUSTRALIA_RELEASE_ID


@pytest.fixture
def data_france_release_id():
    return FRANCE_RELEASE_ID


@pytest.fixture
def data_uae_release_id():
    return UAE_RELEASE_ID


@pytest.fixture
def data_application_json():
    return APPLICATION_JSON
