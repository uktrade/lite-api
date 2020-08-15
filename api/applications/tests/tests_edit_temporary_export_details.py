from django.urls import reverse
from django.utils import timezone
from parameterized import parameterized
from rest_framework import status

from api.applications.enums import ApplicationExportType
from lite_content.lite_api import strings
from api.audit_trail.models import Audit
from cases.enums import CaseTypeEnum
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class EditTemporaryExportDetailsStandardApplication(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_draft_standard_application(self.organisation)
        self.draft.export_type = ApplicationExportType.TEMPORARY
        self.draft.save()
        self.url = reverse("applications:temporary_export_details", kwargs={"pk": self.draft.id})

    def test_perform_action_on_non_temporary_export_type_standard_applications_failure(self):
        permanent_application = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:temporary_export_details", kwargs={"pk": permanent_application.id})
        response = self.client.put(url, {}, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            ["{'get_temp_export_details_update_serializer does not support this export type: permanent'}"],
        )

    def test_perform_action_on_non_open_or_standard_applications_failure(self):
        permanent_application = self.create_mod_clearance_application(
            self.organisation, case_type=CaseTypeEnum.EXHIBITION
        )
        url = reverse("applications:temporary_export_details", kwargs={"pk": permanent_application.id})
        response = self.client.put(url, {}, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"], ["This operation can only be used on applications of type: open, standard"]
        )

    def test_edit_unsubmitted_standard_application_all_temporary_export_details_success(self):
        date = timezone.now().date() + timezone.timedelta(days=2)

        updated_at = self.draft.updated_at

        data = {
            "temp_export_details": "reasons why this export is a temporary one",
            "is_temp_direct_control": False,
            "temp_direct_control_details": "Ukraine govt will be in control whilst product is overseas",
            "proposed_return_date": f"{date.year}-{str(date.month).zfill(2)}-{date.day}",
        }

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(getattr(self.draft, "temp_export_details"), "reasons why this export is a temporary one")
        self.assertNotEqual(self.draft.updated_at, updated_at)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.count(), 0)

    @parameterized.expand(
        [
            [
                {
                    "key": "temp_export_details",
                    "error": strings.Applications.Generic.TemporaryExportDetails.Error.TEMPORARY_EXPORT_DETAILS,
                }
            ],
            [
                {
                    "key": "is_temp_direct_control",
                    "error": strings.Applications.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL,
                }
            ],
            [
                {
                    "key": "proposed_return_date",
                    "error": strings.Applications.Generic.TemporaryExportDetails.Error.PROPOSED_RETURN_DATE_INVALID,
                }
            ],
        ]
    )
    def test_edit_unsubmitted_standard_application_empty_mandatory_field_failure(self, attributes):
        old_attribute = getattr(self.draft, attributes["key"])
        data = {attributes["key"]: ""}

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"][attributes["key"]], [attributes["error"]],
        )

        attribute = getattr(self.draft, attributes["key"])
        self.assertEqual(attribute, old_attribute)

    def test_edit_unsubmitted_standard_application_missing_required_direct_control_details_failure(self):
        data = {
            "is_temp_direct_control": False,
        }

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["temp_direct_control_details"],
            [strings.Applications.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL_MISSING_DETAILS],
        )

    def test_edit_unsubmitted_standard_application_empty_required_direct_control_details_failure(self):
        old_is_temp_direct_control = getattr(self.draft, "is_temp_direct_control")
        old_temp_direct_control_details = getattr(self.draft, "temp_direct_control_details")

        data = {"is_temp_direct_control": False, "temp_direct_control_details": ""}

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["temp_direct_control_details"],
            [strings.Applications.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL_MISSING_DETAILS],
        )
        self.assertEqual(getattr(self.draft, "is_temp_direct_control"), old_is_temp_direct_control)
        self.assertEqual(getattr(self.draft, "temp_direct_control_details"), old_temp_direct_control_details)

    def test_edit_unsubmitted_standard_application_temp_direct_control_field_success(self):
        data = {
            "is_temp_direct_control": True,
        }

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(getattr(self.draft, "is_temp_direct_control"), True)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.count(), 0)

    @parameterized.expand(
        [
            [{"key": "temp_export_details", "value": "reasons why this export is a temporary one"}],
            [{"key": "is_temp_direct_control", "value": False}],
        ]
    )
    def test_edit_submitted_standard_application_temporary_export_details_major_editable(self, attributes):
        self.draft.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.draft.save()

        date = timezone.now().date() + timezone.timedelta(days=2)
        key = attributes["key"]
        value = attributes["value"]

        data = {
            key: value,
            "proposed_return_date": f"{date.year}-{str(date.month).zfill(2)}-{date.day}",
        }

        if "is_temp_direct_control" in data:
            data["temp_direct_control_details"] = "Ukraine govt will be in control whilst product is overseas"

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        attribute = getattr(self.draft, key)
        self.assertEqual(attribute, value)
        if self.draft.is_temp_direct_control is not None:
            self.assertEqual(
                getattr(self.draft, "temp_direct_control_details"),
                "Ukraine govt will be in control whilst product is overseas",
            )
            self.assertEqual(Audit.objects.count(), 3)
        else:
            self.assertEqual(Audit.objects.count(), 2)

    def test_edit_submitted_standard_application_empty_temp_direct_control_details_failure(self):
        self.draft.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.draft.is_temp_direct_control = False
        self.draft.save()

        data = {
            "temp_direct_control_details": "",
        }

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["temp_direct_control_details"],
            [strings.Applications.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL_MISSING_DETAILS],
        )

    def test_edit_submitted_standard_application_proposed_return_date_not_future_failure(self):
        self.draft.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.draft.save()

        data = {"proposed_return_date": timezone.now().date() - timezone.timedelta(days=2)}

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["proposed_return_date"],
            [strings.Applications.Generic.TemporaryExportDetails.Error.PROPOSED_DATE_NOT_IN_FUTURE],
        )

    @parameterized.expand(
        [
            [
                {
                    "key": "temp_export_details",
                    "error": strings.Applications.Generic.TemporaryExportDetails.Error.TEMPORARY_EXPORT_DETAILS,
                }
            ],
            [
                {
                    "key": "is_temp_direct_control",
                    "error": strings.Applications.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL,
                }
            ],
            [
                {
                    "key": "proposed_return_date",
                    "error": strings.Applications.Generic.TemporaryExportDetails.Error.PROPOSED_RETURN_DATE_INVALID,
                }
            ],
        ]
    )
    def test_edit_submitted_standard_application_empty_mandatory_field_failure(self, attributes):
        self.draft.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.draft.save()

        old_attribute = getattr(self.draft, attributes["key"])
        data = {attributes["key"]: ""}

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        attribute = getattr(self.draft, attributes["key"])
        self.assertEqual(attribute, old_attribute)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"][attributes["key"]], [attributes["error"]],
        )


class EditTemporaryExportDetailsOpenApplication(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_draft_open_application(self.organisation)
        self.draft.export_type = ApplicationExportType.TEMPORARY
        self.draft.save()
        self.url = reverse("applications:temporary_export_details", kwargs={"pk": self.draft.id})

    def test_edit_unsubmitted_open_application_all_temporary_export_details_success(self):
        date = timezone.now().date() + timezone.timedelta(days=2)

        updated_at = self.draft.updated_at

        data = {
            "temp_export_details": "reasons why this export is a temporary one",
            "is_temp_direct_control": False,
            "temp_direct_control_details": "Ukraine govt will be in control whilst product is overseas",
            "proposed_return_date": f"{date.year}-{str(date.month).zfill(2)}-{date.day}",
        }

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(getattr(self.draft, "temp_export_details"), "reasons why this export is a temporary one")
        self.assertNotEqual(self.draft.updated_at, updated_at)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.count(), 0)

    @parameterized.expand(
        [
            [
                {
                    "key": "temp_export_details",
                    "error": strings.Applications.Generic.TemporaryExportDetails.Error.TEMPORARY_EXPORT_DETAILS,
                }
            ],
            [
                {
                    "key": "is_temp_direct_control",
                    "error": strings.Applications.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL,
                }
            ],
            [
                {
                    "key": "proposed_return_date",
                    "error": strings.Applications.Generic.TemporaryExportDetails.Error.PROPOSED_RETURN_DATE_INVALID,
                }
            ],
        ]
    )
    def test_edit_unsubmitted_open_application_empty_mandatory_field_failure(self, attributes):
        old_attribute = getattr(self.draft, attributes["key"])
        data = {attributes["key"]: ""}

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"][attributes["key"]], [attributes["error"]],
        )

        attribute = getattr(self.draft, attributes["key"])
        self.assertEqual(attribute, old_attribute)

    def test_edit_unsubmitted_open_application_missing_required_direct_control_details_failure(self):
        data = {
            "is_temp_direct_control": False,
        }

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["temp_direct_control_details"],
            [strings.Applications.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL_MISSING_DETAILS],
        )

    def test_edit_unsubmitted_open_application_empty_required_direct_control_details_failure(self):
        old_is_temp_direct_control = getattr(self.draft, "is_temp_direct_control")
        old_temp_direct_control_details = getattr(self.draft, "temp_direct_control_details")

        data = {"is_temp_direct_control": False, "temp_direct_control_details": ""}

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["temp_direct_control_details"],
            [strings.Applications.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL_MISSING_DETAILS],
        )
        self.assertEqual(getattr(self.draft, "is_temp_direct_control"), old_is_temp_direct_control)
        self.assertEqual(getattr(self.draft, "temp_direct_control_details"), old_temp_direct_control_details)

    def test_edit_unsubmitted_open_application_temp_direct_control_field_success(self):
        data = {
            "is_temp_direct_control": True,
        }

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(getattr(self.draft, "is_temp_direct_control"), True)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.count(), 0)

    @parameterized.expand(
        [
            [{"key": "temp_export_details", "value": "reasons why this export is a temporary one"}],
            [{"key": "is_temp_direct_control", "value": False}],
        ]
    )
    def test_edit_submitted_open_application_temporary_export_details_major_editable(self, attributes):
        self.draft.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.draft.save()

        date = timezone.now().date() + timezone.timedelta(days=2)
        key = attributes["key"]
        value = attributes["value"]

        data = {
            key: value,
            "proposed_return_date": f"{date.year}-{str(date.month).zfill(2)}-{date.day}",
        }

        if "is_temp_direct_control" in data:
            data["temp_direct_control_details"] = "Ukraine govt will be in control whilst product is overseas"

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        attribute = getattr(self.draft, key)
        self.assertEqual(attribute, value)
        if self.draft.is_temp_direct_control is not None:
            self.assertEqual(
                getattr(self.draft, "temp_direct_control_details"),
                "Ukraine govt will be in control whilst product is overseas",
            )
            self.assertEqual(Audit.objects.count(), 3)
        else:
            self.assertEqual(Audit.objects.count(), 2)

    def test_edit_submitted_open_application_empty_temp_direct_control_details_failure(self):
        self.draft.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.draft.is_temp_direct_control = False
        self.draft.save()

        data = {
            "temp_direct_control_details": "",
        }

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["temp_direct_control_details"],
            [strings.Applications.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL_MISSING_DETAILS],
        )

    def test_edit_submitted_open_application_proposed_return_date_not_future_failure(self):
        self.draft.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.draft.save()

        data = {"proposed_return_date": timezone.now().date() - timezone.timedelta(days=2)}

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["proposed_return_date"],
            [strings.Applications.Generic.TemporaryExportDetails.Error.PROPOSED_DATE_NOT_IN_FUTURE],
        )

    @parameterized.expand(
        [
            [
                {
                    "key": "temp_export_details",
                    "error": strings.Applications.Generic.TemporaryExportDetails.Error.TEMPORARY_EXPORT_DETAILS,
                }
            ],
            [
                {
                    "key": "is_temp_direct_control",
                    "error": strings.Applications.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL,
                }
            ],
            [
                {
                    "key": "proposed_return_date",
                    "error": strings.Applications.Generic.TemporaryExportDetails.Error.PROPOSED_RETURN_DATE_INVALID,
                }
            ],
        ]
    )
    def test_edit_submitted_open_application_empty_mandatory_field_failure(self, attributes):
        self.draft.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.draft.save()

        old_attribute = getattr(self.draft, attributes["key"])
        data = {attributes["key"]: ""}

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        attribute = getattr(self.draft, attributes["key"])
        self.assertEqual(attribute, old_attribute)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"][attributes["key"]], [attributes["error"]],
        )
