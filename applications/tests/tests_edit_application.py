from django.urls import reverse
from parameterized import parameterized, parameterized_class
from rest_framework import status

from applications.libraries.case_status_helpers import get_case_statuses
from audit_trail.models import Audit
from audit_trail.payload import AuditType
from cases.enums import CaseTypeEnum
from goods.enums import PvGrading
from lite_content.lite_api import strings
from parties.enums import PartyType
from static.f680_clearance_types.enums import F680ClearanceTypeEnum
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class EditStandardApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.data = {"name": "new app name!"}

    def test_edit_unsubmitted_application_name_success(self):
        """ Test edit the application name of an unsubmitted application. An unsubmitted application
        has the 'draft' status.
        """
        application = self.create_draft_standard_application(self.organisation)

        url = reverse("applications:application", kwargs={"pk": application.id})
        updated_at = application.updated_at

        response = self.client.put(url, self.data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.name, self.data["name"])
        self.assertGreater(application.updated_at, updated_at)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.all().count(), 0)

    @parameterized.expand(get_case_statuses(read_only=False))
    def test_edit_application_name_in_editable_status_success(self, editable_status):
        old_name = "Old Name"
        application = self.create_draft_standard_application(self.organisation, reference_name=old_name)
        self.submit_application(application)
        application.status = get_case_status_by_status(editable_status)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})
        updated_at = application.updated_at
        response = self.client.put(url, self.data, **self.exporter_headers)
        application.refresh_from_db()
        audit_qs = Audit.objects.all()
        audit_object = audit_qs.first()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.name, self.data["name"])
        self.assertNotEqual(application.updated_at, updated_at)
        self.assertEqual(audit_qs.count(), 1)
        self.assertEqual(audit_object.payload, {"new_name": self.data["name"], "old_name": old_name})

    @parameterized.expand(get_case_statuses(read_only=True))
    def test_edit_application_name_in_read_only_status_failure(self, read_only_status):
        application = self.create_draft_standard_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_by_status(read_only_status)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})

        response = self.client.put(url, self.data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_submitted_application_reference_number(self):
        """ Test successful editing of an application's reference number when the application's status
        is non read-only.
        """
        application = self.create_draft_standard_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})
        updated_at = application.updated_at
        audit_qs = Audit.objects.all()
        new_ref = "35236246"
        update_ref = "13124124"

        # Add ref
        data = {"reference_number_on_information_form": new_ref, "have_you_been_informed": "yes"}
        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            application.reference_number_on_information_form, data["reference_number_on_information_form"],
        )
        self.assertNotEqual(application.updated_at, updated_at)

        # Check add audit
        self.assertEqual(audit_qs.count(), 1)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.UPDATE_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": "no reference", "new_ref_number": new_ref})

        # Update ref
        data = {"reference_number_on_information_form": update_ref, "have_you_been_informed": "yes"}
        response = self.client.put(url, data, **self.exporter_headers)

        # Check update audit
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(audit_qs.count(), 2)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.UPDATE_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": new_ref, "new_ref_number": update_ref})

        # Update ref with no reference
        data = {"reference_number_on_information_form": "", "have_you_been_informed": "yes"}
        response = self.client.put(url, data, **self.exporter_headers)

        # Check update
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(audit_qs.count(), 3)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.UPDATE_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": update_ref, "new_ref_number": "no reference"})

        # Remove ref
        data = {"reference_number_on_information_form": "", "have_you_been_informed": "no"}
        response = self.client.put(url, data, **self.exporter_headers)

        # Check update
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(audit_qs.count(), 4)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.REMOVED_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": "no reference"})

    @parameterized.expand(
        [
            [{"key": "military_end_use_controls", "value": True, "reference_number": "48953745ref"}],
            [{"key": "informed_wmd", "value": True, "reference_number": "48953745ref"}],
            [{"key": "suspected_wmd", "value": True, "reference_number": "48953745ref"}],
        ]
    )
    def test_edit_unsubmitted_standard_application_end_use_details(self, attributes):
        application = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:application", kwargs={"pk": application.id})

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
        self.assertEqual(Audit.objects.all().count(), 0)

    @parameterized.expand(
        [
            [{"key": "military_end_use_controls", "value": True, "reference_number": ""}],
            [{"key": "informed_wmd", "value": True, "reference_number": ""}],
            [{"key": "suspected_wmd", "value": True, "reference_number": ""}],
        ]
    )
    def test_edit_unsubmitted_standard_application_end_use_details_mandatory_ref_empty(self, attributes):
        application = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:application", kwargs={"pk": application.id})

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
            response.json()["errors"][reference_key], [strings.Applications.EndUseDetailsErrors.MISSING_REFERENCE]
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
    def test_edit_unsubmitted_standard_application_end_use_details_mandatory_ref_is_none(self, attributes):
        application = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:application", kwargs={"pk": application.id})

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
            (response.json()["errors"][reference_key]), [strings.Applications.EndUseDetailsErrors.MISSING_REFERENCE]
        )

        attribute = getattr(application, key)
        self.assertEqual(attribute, old_attribute)

    @parameterized.expand(
        [
            [
                {
                    "key": "military_end_use_controls",
                    "value": "",
                    "error": strings.Applications.EndUseDetailsErrors.INFORMED_TO_APPLY,
                }
            ],
            [{"key": "informed_wmd", "value": "", "error": strings.Applications.EndUseDetailsErrors.INFORMED_WMD}],
            [{"key": "suspected_wmd", "value": "", "error": strings.Applications.EndUseDetailsErrors.SUSPECTED_WMD}],
        ]
    )
    def test_edit_unsubmitted_standard_application_end_use_details_mandatory_field_is_none(self, attributes):
        application = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:application", kwargs={"pk": application.id})

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
        url = reverse("applications:application", kwargs={"pk": application.id})

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
        self.assertEqual(Audit.objects.all().count(), 2)

    @parameterized.expand(
        [
            [{"key": "is_military_end_use_controls", "value": True}],
            [{"key": "is_informed_wmd", "value": True}],
            [{"key": "is_suspected_wmd", "value": True}],
        ]
    )
    def test_edit_submitted_standard_application_end_use_details_not_major_editable(self, attributes):
        application = self.create_standard_application_case(self.organisation)
        url = reverse("applications:application", kwargs={"pk": application.id})

        key = attributes["key"]
        value = attributes["value"]
        data = {key: value}
        old_attribute = getattr(application, key)

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(response.json()["errors"][key], [strings.Applications.NOT_POSSIBLE_ON_MINOR_EDIT])

        attribute = getattr(application, key)
        self.assertEqual(attribute, old_attribute)

    def test_edit_standard_submitted_application_end_use_details_is_compliant_limitations_eu(self):
        application = self.create_standard_application_case(self.organisation)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})
        data = {
            "is_compliant_limitations_eu": False,
            "compliant_limitations_eu_ref": "24524f",
        }

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.is_compliant_limitations_eu, data["is_compliant_limitations_eu"])
        self.assertEqual(application.compliant_limitations_eu_ref, data["compliant_limitations_eu_ref"])
        self.assertEqual(Audit.objects.all().count(), 1)

    def test_edit_standard_application_end_use_details_is_compliant_limitations_eu_missing(self):
        application = self.create_draft_standard_application(self.organisation)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})
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
            [strings.Applications.EndUseDetailsErrors.IS_COMPLIANT_LIMITATIONS_EU],
        )


class EditOpenApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_draft_open_application(self.organisation)
        self.url = reverse("applications:application", kwargs={"pk": self.application.id})

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
        self.assertEqual(Audit.objects.all().count(), 0)

    @parameterized.expand(
        [
            [{"key": "military_end_use_controls", "value": True, "reference_number": ""}],
            [{"key": "informed_wmd", "value": True, "reference_number": ""}],
            [{"key": "suspected_wmd", "value": True, "reference_number": ""}],
        ]
    )
    def test_edit_unsubmitted_open_application_end_use_details_mandatory_ref_empty(self, attributes):
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
            response.json()["errors"][reference_key], [strings.Applications.EndUseDetailsErrors.MISSING_REFERENCE]
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
    def test_edit_unsubmitted_open_application_end_use_details_mandatory_ref_is_none(self, attributes):
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
            (response.json()["errors"][reference_key]), [strings.Applications.EndUseDetailsErrors.MISSING_REFERENCE]
        )

        attribute = getattr(self.application, key)
        self.assertEqual(attribute, old_attribute)

    @parameterized.expand(
        [
            [
                {
                    "key": "military_end_use_controls",
                    "value": "",
                    "error": strings.Applications.EndUseDetailsErrors.INFORMED_TO_APPLY,
                }
            ],
            [{"key": "informed_wmd", "value": "", "error": strings.Applications.EndUseDetailsErrors.INFORMED_WMD,}],
            [{"key": "suspected_wmd", "value": "", "error": strings.Applications.EndUseDetailsErrors.SUSPECTED_WMD,}],
        ]
    )
    def test_edit_unsubmitted_open_application_end_use_details_mandatory_field_is_none(self, attributes):
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
    def test_edit_submitted_open_application_end_use_details_minor_editable(self, attributes):
        application = self.create_draft_open_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})

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
        self.assertEqual(Audit.objects.all().count(), 2)

    @parameterized.expand(
        [
            [{"key": "is_military_end_use_controls", "value": True}],
            [{"key": "is_informed_wmd", "value": True}],
            [{"key": "is_suspected_wmd", "value": True}],
        ]
    )
    def test_edit_submitted_open_application_end_use_details_not_major_editable(self, attributes):
        application = self.create_draft_open_application(self.organisation)
        self.submit_application(application)
        url = reverse("applications:application", kwargs={"pk": application.id})

        key = attributes["key"]
        old_attribute = getattr(self.application, key)
        value = attributes["value"]
        data = {key: value}

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()["errors"]), 1)
        self.assertEqual(response.json()["errors"][key], [strings.Applications.NOT_POSSIBLE_ON_MINOR_EDIT])

        attribute = getattr(application, key)
        self.assertEqual(attribute, old_attribute)


@parameterized_class(
    "case_type", [(CaseTypeEnum.EXHIBITION,), (CaseTypeEnum.GIFTING,), (CaseTypeEnum.F680,),],
)
class EditMODClearanceApplicationsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_mod_clearance_application(self.organisation, case_type=self.case_type)
        self.url = reverse("applications:application", kwargs={"pk": self.application.id})
        self.data = {"name": "abc"}

    def test_edit_unsubmitted_application_name_success(self):
        updated_at = self.application.updated_at

        response = self.client.put(self.url, self.data, **self.exporter_headers)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.application.name, self.data["name"])
        self.assertNotEqual(self.application.updated_at, updated_at)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.all().count(), 0)

    @parameterized.expand(get_case_statuses(read_only=False))
    def test_edit_application_name_in_editable_status_success(self, editable_status):
        old_name = self.application.name
        self.submit_application(self.application)
        self.application.status = get_case_status_by_status(editable_status)
        self.application.save()
        updated_at = self.application.updated_at

        response = self.client.put(self.url, self.data, **self.exporter_headers)
        self.application.refresh_from_db()
        audit_qs = Audit.objects.all()
        audit_object = audit_qs.first()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.application.name, self.data["name"])
        self.assertNotEqual(self.application.updated_at, updated_at)
        self.assertEqual(audit_qs.count(), 1)
        self.assertEqual(audit_object.payload, {"new_name": self.data["name"], "old_name": old_name})

    @parameterized.expand(get_case_statuses(read_only=True))
    def test_edit_application_name_in_read_only_status_failure(self, read_only_status):
        self.submit_application(self.application)
        self.application.status = get_case_status_by_status(read_only_status)
        self.application.save()

        response = self.client.put(self.url, self.data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EditF680ApplicationsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_mod_clearance_application(self.organisation, case_type=CaseTypeEnum.F680)
        self.url = reverse("applications:application", kwargs={"pk": self.application.id})

    @parameterized.expand(["", "1", "2", "clearance"])
    def test_add_clearance_level_invalid_inputs(self, level):
        data = {"clearance_level": level}

        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([p[0] for p in PvGrading.choices])
    def test_add_clearance_level_success(self, level):
        data = {"clearance_level": level}

        response = self.client.put(self.url, data=data, **self.exporter_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.application.clearance_level, level)

    def test_edit_submitted_application_clearance_level_minor_fail(self):
        """ Test successful editing of an application's reference number when the application's status
        is non read-only.
        """
        application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        url = reverse("applications:application", kwargs={"pk": application.id})
        self.submit_application(application)

        data = {"clearance_level": PvGrading.NATO_CONFIDENTIAL}

        response = self.client.put(url, data=data, **self.exporter_headers)
        self.application.refresh_from_db()
        self.assertEqual(
            response.json()["errors"], {"clearance_level": [strings.Applications.NOT_POSSIBLE_ON_MINOR_EDIT]}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_submitted_application_clearance_level_major_success(self):
        """ Test successful editing of an application's reference number when the application's status
        is non read-only.
        """
        application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        url = reverse("applications:application", kwargs={"pk": application.id})
        self.submit_application(application)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()

        data = {"clearance_level": PvGrading.NATO_CONFIDENTIAL}

        response = self.client.put(url, data=data, **self.exporter_headers)
        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.clearance_level, data["clearance_level"])

    def test_edit_submitted_application_clearance_type_minor_fail(self):
        application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        url = reverse("applications:application", kwargs={"pk": application.id})
        self.submit_application(application)

        data = {"types": [F680ClearanceTypeEnum.MARKET_SURVEY]}
        response = self.client.put(url, data=data, **self.exporter_headers)

        self.application.refresh_from_db()
        self.assertEqual(response.json()["errors"], {"types": [strings.Applications.NOT_POSSIBLE_ON_MINOR_EDIT]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_submitted_application_clearance_type_major_success(self):
        application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        url = reverse("applications:application", kwargs={"pk": application.id})
        self.submit_application(application)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()

        data = {"types": [F680ClearanceTypeEnum.DEMONSTRATION_IN_THE_UK_TO_OVERSEAS_CUSTOMERS]}
        response = self.client.put(url, data=data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            application.types.get().name, F680ClearanceTypeEnum.DEMONSTRATION_IN_THE_UK_TO_OVERSEAS_CUSTOMERS
        )

        # Check add audit
        self.assertEqual(Audit.objects.all().count(), 1)
        audit = Audit.objects.all().first()
        self.assertEqual(AuditType(audit.verb), AuditType.UPDATE_APPLICATION_F680_CLEARANCE_TYPES)
        self.assertEqual(
            audit.payload,
            {
                "old_types": [F680ClearanceTypeEnum.get_text(F680ClearanceTypeEnum.MARKET_SURVEY)],
                "new_types": [F680ClearanceTypeEnum.get_text(type) for type in data["types"]],
            },
        )

    def test_edit_submitted_application_clearance_type_no_data_failure(self):
        application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        url = reverse("applications:application", kwargs={"pk": application.id})
        self.submit_application(application)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()

        data = {"types": []}
        response = self.client.put(url, data=data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"], {"types": [strings.Applications.F680.NO_CLEARANCE_TYPE]},
        )

    def test_add_party_to_f680_success(self):
        party = {
            "type": PartyType.THIRD_PARTY,
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "country": "PY",
            "sub_type": "government",
            "website": "https://www.gov.py",
            "role": "agent",
            "clearance_level": PvGrading.UK_OFFICIAL,
        }
        url = reverse("applications:parties", kwargs={"pk": self.application.id})
        response = self.client.post(url, data=party, **self.exporter_headers)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_party_no_clearance_to_f680_failure(self):
        party = {
            "type": PartyType.THIRD_PARTY,
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "country": "PY",
            "sub_type": "government",
            "website": "https://www.gov.py",
            "role": "agent",
        }
        url = reverse("applications:parties", kwargs={"pk": self.application.id})
        response = self.client.post(url, data=party, **self.exporter_headers)

        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"clearance_level": ["This field is required."]})


class EditExhibitionApplicationsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_mod_clearance_application(self.organisation, case_type=CaseTypeEnum.EXHIBITION)
        self.exhibition_url = reverse("applications:exhibition", kwargs={"pk": self.application.id})

    def test_edit_exhibition_title_in_draft_success(self):
        data = {
            "title": "new_title",
            "required_by_date": self.application.required_by_date,
            "first_exhibition_date": self.application.first_exhibition_date,
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["application"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["title"], data["title"])

    def test_edit_exhibition_title_in_draft_failure_blank(self):
        data = {
            "title": "",
            "required_by_date": self.application.required_by_date,
            "first_exhibition_date": self.application.first_exhibition_date,
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["title"][0], strings.Applications.Exhibition.Error.NO_EXHIBITION_NAME)

    def test_edit_exhibition_title_in_draft_failure_none(self):
        data = {
            "title": None,
            "required_by_date": self.application.required_by_date,
            "first_exhibition_date": self.application.first_exhibition_date,
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["title"][0], strings.Applications.Exhibition.Error.NO_EXHIBITION_NAME)

    def test_edit_exhibition_title_in_draft_failure_not_given(self):
        data = {
            "required_by_date": self.application.required_by_date,
            "first_exhibition_date": self.application.first_exhibition_date,
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["title"][0], strings.Applications.Exhibition.Error.NO_EXHIBITION_NAME)

    def test_edit_exhibition_required_by_date_draft_success(self):
        data = {
            "title": self.application.title,
            "required_by_date": "2020-05-15",
            "first_exhibition_date": self.application.first_exhibition_date,
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["application"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["required_by_date"], data["required_by_date"])

    def test_edit_exhibition_required_by_date_later_than_first_exhibition_date_draft_failure(self):
        data = {
            "title": self.application.title,
            "required_by_date": "2220-05-15",
            "first_exhibition_date": self.application.first_exhibition_date,
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data["first_exhibition_date"][0],
            strings.Applications.Exhibition.Error.REQUIRED_BY_BEFORE_FIRST_EXHIBITION_DATE,
        )

    def test_edit_exhibition_required_by_date_draft_failure_blank(self):
        data = {
            "title": self.application.title,
            "required_by_date": "",
            "first_exhibition_date": self.application.first_exhibition_date,
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data["required_by_date"][0], strings.Applications.Exhibition.Error.BLANK_REQUIRED_BY_DATE,
        )

    def test_edit_exhibition_required_by_date_draft_failure_not_given(self):
        data = {
            "title": self.application.title,
            "first_exhibition_date": self.application.first_exhibition_date,
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data["required_by_date"][0], strings.Applications.Exhibition.Error.NO_REQUIRED_BY_DATE,
        )

    def test_edit_exhibition_required_by_date_draft_failure_none(self):
        data = {
            "title": self.application.title,
            "first_exhibition_date": self.application.first_exhibition_date,
            "required_by_date": None,
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data["required_by_date"][0], strings.Applications.Exhibition.Error.NO_REQUIRED_BY_DATE,
        )

    def test_edit_exhibition_first_exhibition_date_draft_success(self):
        data = {
            "title": self.application.title,
            "required_by_date": self.application.required_by_date,
            "first_exhibition_date": "2022-05-03",
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["application"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["first_exhibition_date"], data["first_exhibition_date"])

    def test_edit_exhibition_first_exhibition_date_draft_failure_before_today(self):
        data = {
            "title": self.application.title,
            "required_by_date": self.application.required_by_date,
            "first_exhibition_date": "2018-05-03",
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data["first_exhibition_date"][0],
            strings.Applications.Exhibition.Error.FIRST_EXHIBITION_DATE_FUTURE,
        )

    def test_can_not_edit_exhibition_details_in_minor_edit(self):
        self.submit_application(self.application)
        # same data as success
        data = {
            "title": "new_title",
            "required_by_date": self.application.required_by_date,
            "first_exhibition_date": self.application.first_exhibition_date,
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data[0],
            f"You can only perform this operation when the application is in a `draft` or "
            f"`{CaseStatusEnum.APPLICANT_EDITING}` state",
        )

    def test_can_edit_exhibition_details_in_major_edit(self):
        self.submit_application(self.application)
        self.application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.application.save()
        # same data as success
        data = {
            "title": "new_title",
            "required_by_date": self.application.required_by_date,
            "first_exhibition_date": self.application.first_exhibition_date,
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)

        response_data = response.json()["application"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["title"], data["title"])

    def test_add_third_party_exhibition_clearance_failure(self):
        party = {
            "type": PartyType.THIRD_PARTY,
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "country": "PY",
            "sub_type": "government",
            "website": "https://www.gov.py",
            "role": "agent",
        }
        url = reverse("applications:parties", kwargs={"pk": self.application.id})
        response = self.client.post(url, data=party, **self.exporter_headers)

        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"bad_request": strings.Parties.BAD_CASE_TYPE})

    def test_add_consignee_exhibition_clearance_failure(self):
        party = {
            "type": PartyType.CONSIGNEE,
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "country": "PY",
            "sub_type": "government",
            "website": "https://www.gov.py",
            "role": "agent",
        }
        url = reverse("applications:parties", kwargs={"pk": self.application.id})
        response = self.client.post(url, data=party, **self.exporter_headers)

        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"bad_request": strings.Parties.BAD_CASE_TYPE})

    def test_add_end_user_exhibition_clearance_failure(self):
        party = {
            "type": PartyType.END_USER,
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "country": "PY",
            "sub_type": "government",
            "website": "https://www.gov.py",
            "role": "agent",
        }
        url = reverse("applications:parties", kwargs={"pk": self.application.id})
        response = self.client.post(url, data=party, **self.exporter_headers)

        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"bad_request": strings.Parties.BAD_CASE_TYPE})

    def test_add_ultimate_end_user_exhibition_clearance_failure(self):
        party = {
            "type": PartyType.ULTIMATE_END_USER,
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "country": "PY",
            "sub_type": "government",
            "website": "https://www.gov.py",
            "role": "agent",
        }
        url = reverse("applications:parties", kwargs={"pk": self.application.id})
        response = self.client.post(url, data=party, **self.exporter_headers)

        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"bad_request": strings.Parties.BAD_CASE_TYPE})
