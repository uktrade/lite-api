import pytest

from freezegun import freeze_time

from api.applications.enums import ApplicationExportType
from api.applications.tests.factories import (
    DraftStandardApplicationFactory,
    StandardApplicationFactory,
)


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def set_time():
    with freeze_time("2023-11-03 12:00:00"):
        yield


def test_permanent_standard_application_reference_code():
    standard_application = StandardApplicationFactory(export_type=ApplicationExportType.PERMANENT)
    assert standard_application.reference_code == "GBSIEL/2023/0000001/P"


def test_temporary_standard_application_reference_code():
    standard_application = StandardApplicationFactory(export_type=ApplicationExportType.TEMPORARY)
    assert standard_application.reference_code == "GBSIEL/2023/0000001/T"


def test_draft_applications_dont_have_reference_codes():
    draft = DraftStandardApplicationFactory()
    assert draft.reference_code is None


def test_reference_code_increment():
    standard_application_1 = StandardApplicationFactory(export_type=ApplicationExportType.PERMANENT)
    assert standard_application_1.reference_code == "GBSIEL/2023/0000001/P"

    standard_application_2 = StandardApplicationFactory(export_type=ApplicationExportType.PERMANENT)
    assert standard_application_2.reference_code == "GBSIEL/2023/0000002/P"
