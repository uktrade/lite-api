import pytest

from rest_framework import status
from rest_framework.exceptions import ErrorDetail

from django.urls import reverse

from api.applications.enums import (
    ApplicationExportLicenceOfficialType,
    ApplicationExportType,
)
from api.applications.models import StandardApplication
from api.cases.enums import (
    CaseTypeEnum,
    CaseTypeReferenceEnum,
)
from api.cases.models import CaseType
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


def test_POST_export_licence_application(
    api_client,
    exporter_headers,
    organisation,
):
    url = reverse("exporter_export_licences:applications")

    response = api_client.post(
        url,
        {
            "name": "Test",
            "export_type": ApplicationExportType.TEMPORARY,
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "123",
            "licence_type": CaseTypeReferenceEnum.SIEL,
        },
        **exporter_headers,
    )

    assert response.status_code == status.HTTP_201_CREATED

    assert StandardApplication.objects.count() == 1

    standard_application = StandardApplication.objects.get()
    assert standard_application.name == "Test"
    assert standard_application.export_type == ApplicationExportType.TEMPORARY
    assert standard_application.have_you_been_informed == ApplicationExportLicenceOfficialType.YES
    assert standard_application.reference_number_on_information_form == "123"
    assert standard_application.organisation == organisation
    assert standard_application.status == get_case_status_by_status(CaseStatusEnum.DRAFT)
    assert standard_application.case_type == CaseType.objects.get(pk=CaseTypeEnum.SIEL.id)

    response_data = response.json()
    assert response_data == {
        "id": str(standard_application.pk),
        "export_type": ApplicationExportType.TEMPORARY,
        "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
        "name": "Test",
        "reference_number_on_information_form": "123",
    }


def test_POST_export_licence_application_empty_export_type_success(
    api_client,
    exporter_headers,
    organisation,
):
    url = reverse("exporter_export_licences:applications")

    response = api_client.post(
        url,
        {
            "name": "Test",
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "123",
            "licence_type": CaseTypeReferenceEnum.SIEL,
        },
        **exporter_headers,
    )

    assert response.status_code == status.HTTP_201_CREATED

    assert StandardApplication.objects.count() == 1

    standard_application = StandardApplication.objects.get()
    assert standard_application.name == "Test"
    assert standard_application.export_type == ""
    assert standard_application.have_you_been_informed == ApplicationExportLicenceOfficialType.YES
    assert standard_application.reference_number_on_information_form == "123"
    assert standard_application.organisation == organisation
    assert standard_application.status == get_case_status_by_status(CaseStatusEnum.DRAFT)
    assert standard_application.case_type == CaseType.objects.get(pk=CaseTypeEnum.SIEL.id)

    response_data = response.json()
    assert response_data == {
        "id": str(standard_application.pk),
        "export_type": "",
        "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
        "name": "Test",
        "reference_number_on_information_form": "123",
    }


def test_POST_export_licence_application_empty_licence_type_default(
    api_client,
    exporter_headers,
    organisation,
):
    url = reverse("exporter_export_licences:applications")

    response = api_client.post(
        url,
        {
            "name": "Test",
            "export_type": ApplicationExportType.TEMPORARY,
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "123",
        },
        **exporter_headers,
    )

    assert response.status_code == status.HTTP_201_CREATED

    assert StandardApplication.objects.count() == 1

    standard_application = StandardApplication.objects.get()
    assert standard_application.name == "Test"
    assert standard_application.export_type == ApplicationExportType.TEMPORARY
    assert standard_application.have_you_been_informed == ApplicationExportLicenceOfficialType.YES
    assert standard_application.reference_number_on_information_form == "123"
    assert standard_application.organisation == organisation
    assert standard_application.status == get_case_status_by_status(CaseStatusEnum.DRAFT)
    assert standard_application.case_type == CaseType.objects.get(pk=CaseTypeEnum.EXPORT_LICENCE.id)

    response_data = response.json()
    assert response_data == {
        "id": str(standard_application.pk),
        "export_type": ApplicationExportType.TEMPORARY,
        "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
        "name": "Test",
        "reference_number_on_information_form": "123",
    }


@pytest.mark.parametrize(
    "data, errors",
    [
        (
            {},
            {
                "name": [ErrorDetail(string="This field is required.", code="required")],
                "have_you_been_informed": [ErrorDetail(string="This field is required.", code="required")],
            },
        ),
        (
            {
                "name": "Test",
                "export_type": "madeup",
                "have_you_been_informed": "madeup",
                "licence_type": "madeup",
            },
            {
                "export_type": [ErrorDetail(string='"madeup" is not a valid choice.', code="invalid_choice")],
                "have_you_been_informed": [
                    ErrorDetail(string='"madeup" is not a valid choice.', code="invalid_choice")
                ],
                "licence_type": [ErrorDetail(string='"madeup" is not a valid choice.', code="invalid_choice")],
            },
        ),
    ],
)
def test_POST_export_licence_application_errors(api_client, exporter_headers, data, errors):
    url = reverse("exporter_export_licences:applications")

    response = api_client.post(
        url,
        data,
        **exporter_headers,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {"errors": errors}

    assert StandardApplication.objects.count() == 0
