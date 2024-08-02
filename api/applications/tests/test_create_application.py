from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse
from urllib.parse import urlencode

from api.applications.enums import ApplicationExportType, ApplicationExportLicenceOfficialType
from api.applications.models import StandardApplication, BaseApplication
from api.applications.tests.factories import DraftStandardApplicationFactory
from api.cases.enums import CaseTypeEnum, CaseTypeReferenceEnum
from lite_content.lite_api import strings
from api.staticdata.trade_control.enums import TradeControlActivity, TradeControlProductCategory
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
            "application_type": CaseTypeReferenceEnum.SIEL,
            "export_type": ApplicationExportType.TEMPORARY,
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "123",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()
        standard_application = StandardApplication.objects.get()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["id"], str(standard_application.id))
        self.assertEqual(StandardApplication.objects.count(), 1)

    def test_create_draft_standard_individual_export_application_empty_export_type_successful(self):
        """
        Ensure we can create a new standard individual export application draft without the export_type field populated
        """
        data = {
            "name": "Test",
            "application_type": CaseTypeReferenceEnum.SIEL,
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "123",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        standard_application = StandardApplication.objects.get()
        self.assertEqual(response_data["id"], str(standard_application.id))
        self.assertEqual(StandardApplication.objects.count(), 1)

    @parameterized.expand(
        [
            [{}],
            [{"application_type": CaseTypeReferenceEnum.SIEL, "export_type": ApplicationExportType.TEMPORARY}],
            [{"name": "Test", "export_type": ApplicationExportType.TEMPORARY}],
            [{"name": "Test", "application_type": CaseTypeReferenceEnum.SIEL}],
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

    def test_create_no_application_type_failure(self):
        """
        Ensure that we cannot create a new application without
        providing a application_type.
        """
        data = {}

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["application_type"][0], strings.Applications.Generic.SELECT_A_LICENCE_TYPE
        )

    def test_trade_control_application(self):
        data = {
            "name": "Test",
            "application_type": CaseTypeEnum.SICL.reference,
            "trade_control_activity": TradeControlActivity.OTHER,
            "trade_control_activity_other": "other activity type",
            "trade_control_product_categories": [key for key, _ in TradeControlProductCategory.choices],
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        application_id = response.json()["id"]
        application = StandardApplication.objects.get(id=application_id)

        self.assertEqual(application.trade_control_activity, data["trade_control_activity"])
        self.assertEqual(application.trade_control_activity_other, data["trade_control_activity_other"])
        self.assertEqual(
            set(application.trade_control_product_categories), set(data["trade_control_product_categories"])
        )

    @parameterized.expand(
        [
            (
                CaseTypeEnum.SICL.reference,
                "trade_control_activity",
                strings.Applications.Generic.TRADE_CONTROL_ACTIVITY_ERROR,
            ),
            (
                CaseTypeEnum.SICL.reference,
                "trade_control_activity_other",
                strings.Applications.Generic.TRADE_CONTROL_ACTIVITY_OTHER_ERROR,
            ),
            (
                CaseTypeEnum.SICL.reference,
                "trade_control_product_categories",
                strings.Applications.Generic.TRADE_CONTROl_PRODUCT_CATEGORY_ERROR,
            ),
        ]
    )
    def test_trade_control_application_failure(self, case_type, missing_field, expected_error):
        data = {
            "name": "Test",
            "application_type": case_type,
            "trade_control_activity": TradeControlActivity.OTHER,
            "trade_control_activity_other": "other activity type",
            "trade_control_product_categories": [key for key, _ in TradeControlProductCategory.choices],
        }
        data.pop(missing_field)

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.json()["errors"]
        self.assertEqual(errors[missing_field], [expected_error])


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
