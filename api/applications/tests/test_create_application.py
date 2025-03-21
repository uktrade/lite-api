from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse
from urllib.parse import urlencode

from api.applications.enums import ApplicationExportType, ApplicationExportLicenceOfficialType
from api.applications.models import StandardApplication, BaseApplication
from api.applications.tests.factories import DraftStandardApplicationFactory
from api.cases.enums import (
    CaseTypeEnum,
    CaseTypeReferenceEnum,
)
from api.cases.models import CaseType
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class DraftTests(DataTestClient):
    url = reverse("applications:applications")

    def test_create_draft_standard_individual_export_application_successful(self):
        """
        Ensure we can create a new standard individual export application draft
        """
        data = {
            "name": "Test",
            "export_type": ApplicationExportType.TEMPORARY,
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "123",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(StandardApplication.objects.count(), 1)

        standard_application = StandardApplication.objects.get()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["id"], str(standard_application.id))
        self.assertEqual(standard_application.name, "Test")
        self.assertEqual(standard_application.export_type, ApplicationExportType.TEMPORARY)
        self.assertEqual(standard_application.have_you_been_informed, ApplicationExportLicenceOfficialType.YES)
        self.assertEqual(standard_application.reference_number_on_information_form, "123")
        self.assertEqual(standard_application.organisation, self.organisation)
        self.assertEqual(standard_application.status, get_case_status_by_status(CaseStatusEnum.DRAFT))
        self.assertEqual(standard_application.case_type, CaseType.objects.get(pk=CaseTypeEnum.SIEL.id))

    def test_create_draft_standard_individual_export_application_empty_export_type_successful(self):
        """
        Ensure we can create a new standard individual export application draft without the export_type field populated
        """
        data = {
            "name": "Test",
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "123",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(StandardApplication.objects.count(), 1)
        standard_application = StandardApplication.objects.get()
        self.assertEqual(response_data["id"], str(standard_application.id))
        self.assertEqual(standard_application.name, "Test")
        self.assertEqual(standard_application.export_type, "")
        self.assertEqual(standard_application.have_you_been_informed, ApplicationExportLicenceOfficialType.YES)
        self.assertEqual(standard_application.reference_number_on_information_form, "123")
        self.assertEqual(standard_application.organisation, self.organisation)
        self.assertEqual(standard_application.status, get_case_status_by_status(CaseStatusEnum.DRAFT))
        self.assertEqual(standard_application.case_type, CaseType.objects.get(pk=CaseTypeEnum.SIEL.id))

    @parameterized.expand(
        [
            [{}],
            [{"export_type": ApplicationExportType.TEMPORARY}],
            [{"name": "Test", "export_type": ApplicationExportType.TEMPORARY}],
            [{"name": "Test"}],
            [{"application_type": CaseTypeReferenceEnum.EXHC}],
            [{"name": "Test"}],
        ]
    )
    def test_create_draft_failure(self, data):
        """
        Ensure we cannot create a new draft object with POST data that is missing required properties
        Applications require: application_type, export_type & name
        Exhibition clearances require: application_type & name
        Above is a mixture of invalid combinations for these cases
        """
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(BaseApplication.objects.count(), 0)


class ApplicationsListTests(DataTestClient):
    url = reverse("applications:applications")

    @parameterized.expand(
        [
            [
                {"num_drafts": 10},
                {"status": "submitted", "count": 2},
                [
                    {"selected_filter": "draft_applications", "expected": 8},
                    {"selected_filter": "submitted_applications", "expected": 2},
                    {"selected_filter": "archived_applications", "expected": 0},
                ],
            ],
            [
                {"num_drafts": 10},
                {"status": "submitted", "count": 4},
                [
                    {"selected_filter": "draft_tab", "expected": 6},
                    {"selected_filter": "submitted_applications", "expected": 4},
                ],
            ],
            [
                {"num_drafts": 10},
                {"status": "finalised", "count": 5},
                [
                    {"selected_filter": "finalised_applications", "expected": 5},
                    {"selected_filter": "draft_applications", "expected": 5},
                ],
            ],
            [
                {"num_drafts": 10},
                {"status": "superseded_by_exporter_edit", "count": 3},
                [
                    {"selected_filter": "archived_applications", "expected": 3},
                    {"selected_filter": "draft_applications", "expected": 7},
                    {"selected_filter": "finalised_applications", "expected": 0},
                ],
            ],
        ]
    )
    def test_retrieve_applications_tests(self, initial, target_state, filters):
        drafts = [
            DraftStandardApplicationFactory(
                organisation=self.organisation,
            )
            for _ in range(initial["num_drafts"])
        ]

        for draft in drafts[: target_state["count"]]:
            draft.status = get_case_status_by_status(target_state["status"])
            draft.save()

        for filter in filters:
            expected_count = filter.pop("expected")

            url = f"{self.url}?{urlencode(filter, doseq=True)}"
            response = self.client.get(url, **self.exporter_headers)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response = response.json()
            self.assertEqual(len(response["results"]), expected_count)
