from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import CaseTypeEnum
from lite_content.lite_api import strings
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class EditStandardApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.data = {"name": "new app name!"}

    @parameterized.expand(
        [
            [{"key": "military_end_use_controls", "value": True, "reference_number": "48953745ref"}],
            [{"key": "informed_wmd", "value": True, "reference_number": "48953745ref"}],
            [{"key": "suspected_wmd", "value": True, "reference_number": "48953745ref"}],
        ]
    )
    def test_edit_unsubmitted_standard_application_end_use_details(self, attributes):
        application = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})

        key = "is_" + attributes["key"]
        value = attributes["value"]
        data = {key: value}
        reference_key = attributes["key"] + "_ref"
        data[reference_key] = attributes["reference_number"]

        updated_at = application.updated_at

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        attribute = getattr(application, key)
        self.assertEqual(attribute, value)

        self.assertNotEqual(application.updated_at, updated_at)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.count(), 0)

    @parameterized.expand(
        [
            [{"key": "military_end_use_controls", "value": True, "reference_number": ""}],
            [{"key": "informed_wmd", "value": True, "reference_number": ""}],
            [{"key": "suspected_wmd", "value": True, "reference_number": ""}],
        ]
    )
    def test_edit_unsubmitted_standard_application_end_use_details_mandatory_ref_is_empty(self, attributes):
        application = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})

        key = "is_" + attributes["key"]
        value = attributes["value"]
        data = {key: value}
        old_attribute = getattr(application, key)

        reference_key = attributes["key"] + "_ref"
        data[reference_key] = attributes["reference_number"]

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"][reference_key],
            [strings.Applications.Generic.EndUseDetails.Error.MISSING_DETAILS],
        )

        attribute = getattr(application, key)
        self.assertEqual(attribute, old_attribute)

    @parameterized.expand(
        [
            [{"key": "military_end_use_controls", "value": True}],
            [{"key": "informed_wmd", "value": True}],
            [{"key": "suspected_wmd", "value": True}],
        ]
    )
    def test_edit_unsubmitted_standard_application_end_use_details_mandatory_ref_is_missing(self, attributes):
        application = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})

        key = "is_" + attributes["key"]
        value = attributes["value"]
        data = {key: value}
        reference_key = attributes["key"] + "_ref"
        old_attribute = getattr(application, key)

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            (response.json()["errors"][reference_key]),
            [strings.Applications.Generic.EndUseDetails.Error.MISSING_DETAILS],
        )

        attribute = getattr(application, key)
        self.assertEqual(attribute, old_attribute)

    @parameterized.expand(
        [
            [
                {
                    "key": "military_end_use_controls",
                    "value": "",
                    "error": strings.Applications.Generic.EndUseDetails.Error.INFORMED_TO_APPLY,
                }
            ],
            [
                {
                    "key": "informed_wmd",
                    "value": "",
                    "error": strings.Applications.Generic.EndUseDetails.Error.INFORMED_WMD,
                }
            ],
            [
                {
                    "key": "suspected_wmd",
                    "value": "",
                    "error": strings.Applications.Generic.EndUseDetails.Error.SUSPECTED_WMD,
                }
            ],
        ]
    )
    def test_edit_unsubmitted_standard_application_end_use_details_mandatory_field_is_empty(self, attributes):
        application = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})

        key = "is_" + attributes["key"]
        value = attributes["value"]
        data = {key: value}
        old_attribute = getattr(application, key)

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(response.json()["errors"][key], [attributes["error"]])

        attribute = getattr(application, key)
        self.assertEqual(attribute, old_attribute)

    @parameterized.expand(
        [
            [{"key": "military_end_use_controls", "value": True, "reference_number": "hadd"}],
            [{"key": "informed_wmd", "value": True, "reference_number": "kjjdnsk"}],
            [{"key": "suspected_wmd", "value": True, "reference_number": "kjndskhjds"}],
        ]
    )
    def test_edit_submitted_standard_application_end_use_details_major_editable(self, attributes):
        application = self.create_standard_application_case(self.organisation)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})

        key = "is_" + attributes["key"]
        value = attributes["value"]
        reference_key = attributes["key"] + "_ref"
        reference_value = attributes["reference_number"]

        data = {key: value, reference_key: reference_value}

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        attribute = getattr(application, key)
        self.assertEqual(attribute, value)
        self.assertEqual(Audit.objects.count(), 3)

    @parameterized.expand(
        [
            [{"key": "is_military_end_use_controls", "value": True, "reference_number": "hadd"}],
            [{"key": "is_informed_wmd", "value": True, "reference_number": "kjjdnsk"}],
            [{"key": "is_suspected_wmd", "value": True, "reference_number": "kjndskhjds"}],
        ]
    )
    def test_edit_submitted_standard_application_end_use_details_not_major_editable(self, attributes):
        application = self.create_standard_application_case(self.organisation)
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})

        key = attributes["key"]
        value = attributes["value"]
        data = {key: value}
        old_attribute = getattr(application, key)

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["non_field_errors"],
            [strings.Applications.Generic.INVALID_OPERATION_FOR_NON_DRAFT_OR_MAJOR_EDIT_CASE_ERROR],
        )

        attribute = getattr(application, key)
        self.assertEqual(attribute, old_attribute)

    def test_edit_standard_submitted_application_end_use_details_is_compliant_limitations_eu(self):
        application = self.create_standard_application_case(self.organisation)
        application.is_eu_military = True
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})
        data = {
            "is_compliant_limitations_eu": False,
            "compliant_limitations_eu_ref": "24524f",
        }

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.is_compliant_limitations_eu, data["is_compliant_limitations_eu"])
        self.assertEqual(application.compliant_limitations_eu_ref, data["compliant_limitations_eu_ref"])
        self.assertEqual(Audit.objects.count(), 3)

    def test_edit_standard_application_end_use_details_is_compliant_limitations_eu_is_empty(self):
        application = self.create_draft_standard_application(self.organisation)
        application.is_eu_military = True
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})
        data = {
            "is_compliant_limitations_eu": "",
            "compliant_limitations_eu_ref": "",
        }

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["is_compliant_limitations_eu"],
            [strings.Applications.Generic.EndUseDetails.Error.COMPLIANT_LIMITATIONS_EU],
        )

    def test_edit_standard_application_end_use_details_intended_end_use(self):
        application = self.create_draft_standard_application(self.organisation)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})
        data = {
            "intended_end_use": "this is the intended end use",
        }

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.intended_end_use, data["intended_end_use"])
        self.assertEqual(Audit.objects.count(), 1)

    def test_edit_standard_application_end_use_details_intended_end_use_is_empty(self):
        application = self.create_draft_standard_application(self.organisation)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})
        data = {
            "intended_end_use": "",
        }

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["intended_end_use"],
            [strings.Applications.Generic.EndUseDetails.Error.INTENDED_END_USE],
        )


class EditOpenApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_draft_open_application(self.organisation)
        self.url = reverse("applications:end_use_details", kwargs={"pk": self.application.id})

    @parameterized.expand(
        [
            [{"key": "military_end_use_controls", "value": True, "reference_number": "48953745ref"}],
            [{"key": "informed_wmd", "value": True, "reference_number": "48953745ref"}],
            [{"key": "suspected_wmd", "value": True, "reference_number": "48953745ref"}],
        ]
    )
    def test_edit_unsubmitted_open_application_end_use_details(self, attributes):
        key = "is_" + attributes["key"]
        value = attributes["value"]
        data = {key: value}

        if "reference_number" in attributes:
            reference_key = attributes["key"] + "_ref"
            data[reference_key] = attributes["reference_number"]

        updated_at = self.application.updated_at

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        attribute = getattr(self.application, key)
        self.assertEqual(attribute, value)

        self.assertNotEqual(self.application.updated_at, updated_at)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.count(), 0)

    @parameterized.expand(
        [
            [{"key": "military_end_use_controls", "value": True, "reference_number": ""}],
            [{"key": "informed_wmd", "value": True, "reference_number": ""}],
            [{"key": "suspected_wmd", "value": True, "reference_number": ""}],
        ]
    )
    def test_edit_unsubmitted_open_application_end_use_details_mandatory_ref_is_empty(self, attributes):
        key = "is_" + attributes["key"]
        old_attribute = getattr(self.application, key)
        value = attributes["value"]
        data = {key: value}

        reference_key = attributes["key"] + "_ref"
        data[reference_key] = attributes["reference_number"]

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"][reference_key],
            [strings.Applications.Generic.EndUseDetails.Error.MISSING_DETAILS],
        )

        attribute = getattr(self.application, key)
        self.assertEqual(attribute, old_attribute)

    @parameterized.expand(
        [
            [{"key": "military_end_use_controls", "value": True}],
            [{"key": "informed_wmd", "value": True}],
            [{"key": "suspected_wmd", "value": True}],
        ]
    )
    def test_edit_unsubmitted_open_application_end_use_details_mandatory_ref_is_missing(self, attributes):
        key = "is_" + attributes["key"]
        old_attribute = getattr(self.application, key)
        value = attributes["value"]
        data = {key: value}
        reference_key = attributes["key"] + "_ref"

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            (response.json()["errors"][reference_key]),
            [strings.Applications.Generic.EndUseDetails.Error.MISSING_DETAILS],
        )

        attribute = getattr(self.application, key)
        self.assertEqual(attribute, old_attribute)

    @parameterized.expand(
        [
            [
                {
                    "key": "military_end_use_controls",
                    "value": "",
                    "error": strings.Applications.Generic.EndUseDetails.Error.INFORMED_TO_APPLY,
                }
            ],
            [
                {
                    "key": "informed_wmd",
                    "value": "",
                    "error": strings.Applications.Generic.EndUseDetails.Error.INFORMED_WMD,
                }
            ],
            [
                {
                    "key": "suspected_wmd",
                    "value": "",
                    "error": strings.Applications.Generic.EndUseDetails.Error.SUSPECTED_WMD,
                }
            ],
        ]
    )
    def test_edit_unsubmitted_open_application_end_use_details_mandatory_field_is_empty(self, attributes):
        key = "is_" + attributes["key"]
        old_attribute = getattr(self.application, key)
        value = attributes["value"]
        data = {key: value}

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(response.json()["errors"][key], [attributes["error"]])

        attribute = getattr(self.application, key)
        self.assertEqual(attribute, old_attribute)

    @parameterized.expand(
        [
            [{"key": "military_end_use_controls", "value": True, "reference_number": "hadd"}],
            [{"key": "informed_wmd", "value": True, "reference_number": "kjjdnsk"}],
            [{"key": "suspected_wmd", "value": True, "reference_number": "kjndskhjds"}],
        ]
    )
    def test_edit_submitted_open_application_end_use_details_major_editable(self, attributes):
        application = self.create_draft_open_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})

        key = "is_" + attributes["key"]
        value = attributes["value"]
        reference_key = attributes["key"] + "_ref"
        reference_value = attributes["reference_number"]

        data = {key: value, reference_key: reference_value}

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        attribute = getattr(application, key)
        self.assertEqual(attribute, value)
        self.assertEqual(Audit.objects.count(), 3)

    @parameterized.expand(
        [
            [{"key": "is_military_end_use_controls", "value": True, "reference_number": "hadd"}],
            [{"key": "is_informed_wmd", "value": True, "reference_number": "kjjdnsk"}],
            [{"key": "is_suspected_wmd", "value": True, "reference_number": "kjndskhjds"}],
        ]
    )
    def test_edit_submitted_open_application_end_use_details_not_major_editable(self, attributes):
        application = self.create_draft_open_application(self.organisation)
        self.submit_application(application)
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})

        key = attributes["key"]
        old_attribute = getattr(self.application, key)
        value = attributes["value"]
        data = {key: value}

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["non_field_errors"],
            [strings.Applications.Generic.INVALID_OPERATION_FOR_NON_DRAFT_OR_MAJOR_EDIT_CASE_ERROR],
        )

        attribute = getattr(application, key)
        self.assertEqual(attribute, old_attribute)

    def test_edit_open_application_end_use_details_intended_end_use(self):
        application = self.create_draft_open_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})
        data = {
            "intended_end_use": "this is the intended end use",
        }

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.intended_end_use, data["intended_end_use"])
        self.assertEqual(Audit.objects.count(), 2)

    def test_edit_open_application_end_use_details_intended_end_use_is_empty(self):
        application = self.create_draft_open_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:end_use_details", kwargs={"pk": application.id})
        data = {
            "intended_end_use": "",
        }

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["intended_end_use"],
            [strings.Applications.Generic.EndUseDetails.Error.INTENDED_END_USE],
        )


class EditF680ApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_mod_clearance_application(self.organisation, case_type=CaseTypeEnum.F680)
        self.url = reverse("applications:end_use_details", kwargs={"pk": self.application.id})

    def test_edit_f680_application_end_use_details_intended_end_use(self):
        self.application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.application.save()

        data = {
            "intended_end_use": "this is the intended end use",
        }

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.application.intended_end_use, data["intended_end_use"])
        self.assertEqual(Audit.objects.count(), 1)

    def test_edit_f680_application_end_use_details_intended_end_use_is_empty_failure(self):
        self.submit_application(self.application)
        self.application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.application.save()

        data = {
            "intended_end_use": "",
        }

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(
            response.json()["errors"]["intended_end_use"],
            [strings.Applications.Generic.EndUseDetails.Error.INTENDED_END_USE],
        )
