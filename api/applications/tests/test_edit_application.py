import datetime

from django.urls import reverse
from parameterized import parameterized, parameterized_class
from rest_framework import status

from api.applications.libraries.case_status_helpers import get_case_statuses
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import CaseTypeEnum
from api.goods.enums import PvGrading
from lite_content.lite_api import strings
from api.parties.enums import PartyType, SubType
from api.staticdata.f680_clearance_types.enums import F680ClearanceTypeEnum
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class EditStandardApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.data = {"name": "new app name!"}

    def test_edit_unsubmitted_application_name_success(self):
        """Test edit the application name of an unsubmitted application. An unsubmitted application
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
        self.assertEqual(Audit.objects.count(), 0)

    def test_edit_unsubmitted_application_export_type_success(self):
        """Test edit the application export_type of an unsubmitted application. An unsubmitted application
        has the 'draft' status.
        """
        application = self.create_draft_standard_application(self.organisation)
        # export_type is set to permanent in create_draft_standard_application
        self.assertEqual(application.export_type, "permanent")

        url = reverse("applications:application", kwargs={"pk": application.id})
        updated_at = application.updated_at

        response = self.client.put(url, {"export_type": "temporary"}, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.export_type, "temporary")
        self.assertGreater(application.updated_at, updated_at)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.count(), 0)

    def test_edit_unsubmitted_application_locations_success(self):
        application = self.create_draft_standard_application(self.organisation)

        url = reverse("applications:application", kwargs={"pk": application.id})
        updated_at = application.updated_at

        data = {
            "goods_starting_point": "GB",
            "goods_recipients": "via_consignee",
        }

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.goods_starting_point, "GB")
        self.assertEqual(application.goods_recipients, "via_consignee")
        self.assertGreater(application.updated_at, updated_at)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.count(), 0)

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
        self.assertEqual(audit_qs.count(), 2)
        self.assertEqual(audit_object.verb, AuditType.UPDATED_APPLICATION_NAME)
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
        """Test successful editing of an application's reference number when the application's status
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
            application.reference_number_on_information_form,
            data["reference_number_on_information_form"],
        )
        self.assertNotEqual(application.updated_at, updated_at)

        # Check add audit
        self.assertEqual(audit_qs.count(), 2)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.UPDATE_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": "no reference", "new_ref_number": new_ref})

        # Update ref
        data = {"reference_number_on_information_form": update_ref, "have_you_been_informed": "yes"}
        response = self.client.put(url, data, **self.exporter_headers)

        # Check update audit
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(audit_qs.count(), 3)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.UPDATE_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": new_ref, "new_ref_number": update_ref})

        # Update ref with no reference
        data = {"reference_number_on_information_form": "", "have_you_been_informed": "yes"}
        response = self.client.put(url, data, **self.exporter_headers)

        # Check update
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(audit_qs.count(), 4)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.UPDATE_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": update_ref, "new_ref_number": "no reference"})

        # Remove ref
        data = {"reference_number_on_information_form": "", "have_you_been_informed": "no"}
        response = self.client.put(url, data, **self.exporter_headers)

        # Check update
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(audit_qs.count(), 5)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.REMOVED_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": "no reference"})


@parameterized_class(
    "case_type",
    [
        (CaseTypeEnum.EXHIBITION,),
        (CaseTypeEnum.GIFTING,),
        (CaseTypeEnum.F680,),
    ],
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
        self.assertEqual(Audit.objects.count(), 0)

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
        self.assertEqual(audit_qs.count(), 2)
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
        """Test successful editing of an application's reference number when the application's status
        is non read-only.
        """
        application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        url = reverse("applications:application", kwargs={"pk": application.id})
        self.submit_application(application)

        data = {"clearance_level": PvGrading.NATO_CONFIDENTIAL}

        response = self.client.put(url, data=data, **self.exporter_headers)
        self.application.refresh_from_db()
        self.assertEqual(
            response.json()["errors"], {"clearance_level": [strings.Applications.Generic.NOT_POSSIBLE_ON_MINOR_EDIT]}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_submitted_application_clearance_level_major_success(self):
        """Test successful editing of an application's reference number when the application's status
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
        self.assertEqual(
            response.json()["errors"], {"types": [strings.Applications.Generic.NOT_POSSIBLE_ON_MINOR_EDIT]}
        )
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
        self.assertEqual(Audit.objects.all().count(), 2)
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
            response.json()["errors"],
            {"types": [strings.Applications.F680.NO_CLEARANCE_TYPE]},
        )

    def test_add_party_to_f680_success(self):
        party = {
            "type": PartyType.THIRD_PARTY,
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "country": "PY",
            "sub_type": SubType.GOVERNMENT,
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
        required_by_date = datetime.date.today() + datetime.timedelta(days=5)
        required_by_date = required_by_date.isoformat()

        data = {
            "title": self.application.title,
            "required_by_date": required_by_date,
            "first_exhibition_date": self.application.first_exhibition_date,
        }

        response = self.client.post(self.exhibition_url, data=data, **self.exporter_headers)
        response_data = response.json()["application"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["required_by_date"], required_by_date)

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
            response_data["required_by_date"][0],
            strings.Applications.Exhibition.Error.BLANK_REQUIRED_BY_DATE,
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
            response_data["required_by_date"][0],
            strings.Applications.Exhibition.Error.NO_REQUIRED_BY_DATE,
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
            response_data["required_by_date"][0],
            strings.Applications.Exhibition.Error.NO_REQUIRED_BY_DATE,
        )

    def test_edit_exhibition_first_exhibition_date_draft_success(self):
        data = {
            "title": self.application.title,
            "required_by_date": self.application.required_by_date,
            "first_exhibition_date": "2030-08-03",
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

        response_data = response.json()["errors"]["non_field_errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data,
            [strings.Applications.Generic.INVALID_OPERATION_FOR_NON_DRAFT_OR_MAJOR_EDIT_CASE_ERROR],
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
        self.assertEqual(response.json()["errors"], {"bad_request": strings.PartyErrors.BAD_CASE_TYPE})

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
        self.assertEqual(response.json()["errors"], {"bad_request": strings.PartyErrors.BAD_CASE_TYPE})

    def test_add_end_user_exhibition_clearance_failure(self):
        party = {
            "type": PartyType.END_USER,
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "signatory_name_euu": "Government of Paraguay",
            "country": "PY",
            "sub_type": "government",
            "website": "https://www.gov.py",
            "role": "agent",
        }
        url = reverse("applications:parties", kwargs={"pk": self.application.id})
        response = self.client.post(url, data=party, **self.exporter_headers)

        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"bad_request": strings.PartyErrors.BAD_CASE_TYPE})

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
        self.assertEqual(response.json()["errors"], {"bad_request": strings.PartyErrors.BAD_CASE_TYPE})
