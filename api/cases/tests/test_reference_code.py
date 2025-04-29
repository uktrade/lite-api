import pytest

from freezegun import freeze_time

from api.applications.enums import ApplicationExportType
from api.applications.tests.factories import (
    DraftStandardApplicationFactory,
    StandardApplicationFactory,
)
from api.f680.tests.factories import (
    F680ApplicationFactory,
    SubmittedF680ApplicationFactory,
)


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def set_time():
    with freeze_time("2023-11-03 12:00:00"):
        yield


@pytest.mark.parametrize(
    "application_factory, factory_kwargs, expected_reference_code",
    (
        (DraftStandardApplicationFactory, {}, None),
        (StandardApplicationFactory, {"export_type": ApplicationExportType.PERMANENT}, "GBSIEL/2023/0000001/P"),
        (StandardApplicationFactory, {"export_type": ApplicationExportType.TEMPORARY}, "GBSIEL/2023/0000001/T"),
        (F680ApplicationFactory, {}, None),
        (SubmittedF680ApplicationFactory, {}, "F680/2023/0000001"),
    ),
)
def test_reference_code(application_factory, factory_kwargs, expected_reference_code):
    application = application_factory(**factory_kwargs)
    assert application.reference_code == expected_reference_code


def test_reference_code_increment():
    standard_application_1 = StandardApplicationFactory(export_type=ApplicationExportType.PERMANENT)
    assert standard_application_1.reference_code == "GBSIEL/2023/0000001/P"

    standard_application_2 = StandardApplicationFactory(export_type=ApplicationExportType.PERMANENT)
    assert standard_application_2.reference_code == "GBSIEL/2023/0000002/P"
