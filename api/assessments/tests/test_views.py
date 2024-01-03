from datetime import datetime

from django.urls import reverse
from freezegun import freeze_time
import pytest
from rest_framework import status

from test_helpers.clients import DataTestClient
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.goods.enums import GoodStatus
from api.goods.tests.factories import GoodFactory
from api.applications.models import GoodOnApplication
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.report_summaries.models import ReportSummarySubject, ReportSummaryPrefix
from api.staticdata.statuses.models import CaseStatus

from lite_content.lite_api import strings


class MakeAssessmentsViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_draft_standard_application(organisation=self.organisation)
        self.case = self.submit_application(self.application)
        self.good = GoodFactory(organisation=self.organisation)
        self.good_on_application = GoodOnApplication.objects.create(
            good=self.good, application=self.application, quantity=10, value=500
        )
        self.good_on_application_2 = GoodOnApplication.objects.create(
            good=self.good, application=self.application, quantity=10, value=500
        )
        self.good_on_application_3 = GoodOnApplication.objects.create(
            good=self.good, application=self.application, quantity=10, value=500
        )
        self.assessment_url = reverse("assessments:make_assessments", kwargs={"case_pk": self.case.id})

    def test_empty_data_success(self):
        data = []
        response = self.client.put(self.assessment_url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_controlled_goods_must_have_report_summary_subject(self):
        # Setting is_good_controlled to True requires a report_summary_subject to be non None
        # verify that if this condition raises a ValidationError
        regime_entry = RegimeEntry.objects.first()
        report_summary_prefix = ReportSummaryPrefix.objects.first()
        data = [
            {
                "id": self.good_on_application.id,
                "control_list_entries": [],
                "regime_entries": [regime_entry.id],
                "report_summary_prefix": report_summary_prefix.id,
                "report_summary_subject": None,
                "is_good_controlled": True,
                "comment": "some comment",
                "report_summary": "some string we expect to be overwritten",
                "is_ncsc_military_information_security": True,
            }
        ]
        response = self.client.put(self.assessment_url, data, **self.gov_headers)
        expected_response_data = {"errors": [{"report_summary_subject": [strings.Picklists.REQUIRED_REPORT_SUMMARY]}]}

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.json(), expected_response_data)

    def test_legacy_goods_are_allowed(self):
        # Legacy GoodOnApplications have a report_summary but no report_summary_subject or report_summary_prefix
        good_on_application = self.good_on_application
        regime_entry = RegimeEntry.objects.first()
        data = [
            {
                "id": self.good_on_application.id,
                "control_list_entries": [],
                "regime_entries": [regime_entry.id],
                "report_summary_prefix": None,
                "report_summary_subject": None,
                "is_good_controlled": True,
                "comment": "some comment",
                "report_summary": "some legacy summary",
                "is_ncsc_military_information_security": True,
            }
        ]
        response = self.client.put(self.assessment_url, data, **self.gov_headers)

        assert response.status_code == status.HTTP_200_OK
        good_on_application.refresh_from_db()

        assert good_on_application.report_summary == "some legacy summary"
        assert good_on_application.report_summary_prefix is None
        assert good_on_application.report_summary_subject is None

    @freeze_time("2023-11-03 12:00:00")
    def test_valid_data_updates_single_record(self):
        good_on_application = self.good_on_application
        regime_entry = RegimeEntry.objects.first()
        report_summary_prefix = ReportSummaryPrefix.objects.first()
        report_summary_subject = ReportSummarySubject.objects.first()
        data = [
            {
                "id": self.good_on_application.id,
                "control_list_entries": ["ML1"],
                "regime_entries": [regime_entry.id],
                "report_summary_prefix": report_summary_prefix.id,
                "report_summary_subject": report_summary_subject.id,
                "is_good_controlled": True,
                "comment": "some comment",
                "report_summary": "some string we expect to be overwritten",
                "is_ncsc_military_information_security": True,
            }
        ]
        response = self.client.put(self.assessment_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        good_on_application.refresh_from_db()
        all_cles = [cle.rating for cle in good_on_application.control_list_entries.all()]
        assert all_cles == ["ML1"]
        all_regime_entries = [regime_entry.id for regime_entry in good_on_application.regime_entries.all()]
        assert all_regime_entries == [regime_entry.id]
        assert good_on_application.report_summary_prefix_id == report_summary_prefix.id
        assert good_on_application.report_summary_subject_id == report_summary_subject.id
        assert good_on_application.is_good_controlled == True
        assert good_on_application.comment == "some comment"
        assert good_on_application.is_ncsc_military_information_security == True
        assert good_on_application.report_summary == f"{report_summary_prefix.name} {report_summary_subject.name}"
        assert good_on_application.assessed_by == self.gov_user
        assert good_on_application.assessment_date.isoformat() == "2023-11-03T12:00:00+00:00"

        good = good_on_application.good
        assert good.status == GoodStatus.VERIFIED
        assert [cle.rating for cle in good.control_list_entries.all()] == ["ML1"]
        assert good_on_application.report_summary == f"{report_summary_prefix.name} {report_summary_subject.name}"
        assert good.report_summary_prefix_id == report_summary_prefix.id
        assert good.report_summary_subject_id == report_summary_subject.id

        audit_entry = Audit.objects.order_by("-created_at").get(verb=AuditType.PRODUCT_REVIEWED)
        assert audit_entry.payload == {
            "additional_text": "some comment",
            "good_name": good.name,
            "line_no": 2,  # We have another GoodOnApplication which we are not using for the test, so this will be 2
            "new_control_list_entry": ["ML1"],
            "new_is_good_controlled": "Yes",
            "new_regime_entries": [regime_entry.name],
            "old_control_list_entry": ["No control code"],
            "old_is_good_controlled": "No",
            "old_regime_entries": ["No regimes"],
            "old_report_summary": None,
            "report_summary": good_on_application.report_summary,
        }

    def test_making_a_good_uncontrolled_clears_report_fields(self):
        # Setting is_good_controlled to False should set report_summary_prefix and report_summary_subject to None
        good_on_application = self.good_on_application
        regime_entry = RegimeEntry.objects.first()
        report_summary_subject = ReportSummarySubject.objects.first()
        report_summary_prefix = ReportSummaryPrefix.objects.first()
        data = [
            {
                "id": self.good_on_application.id,
                "control_list_entries": ["ML1"],
                "regime_entries": [regime_entry.id],
                "report_summary_prefix": report_summary_prefix.id,
                "report_summary_subject": report_summary_subject.id,
                "is_good_controlled": True,
                "comment": "some comment",
                "report_summary": "some string we expect to be overwritten",
                "is_ncsc_military_information_security": True,
            }
        ]
        response = self.client.put(self.assessment_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data[0]["is_good_controlled"] = False
        response = self.client.put(self.assessment_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        good_on_application.refresh_from_db()

        assert good_on_application.report_summary_prefix_id is None
        assert good_on_application.report_summary_subject_id is None

    @freeze_time("2023-11-03 12:00:00")
    def test_valid_data_updates_single_record_on_already_verified_good(self):
        good_on_application = self.good_on_application
        self.good.status = GoodStatus.VERIFIED
        self.good.control_list_entries.set([ControlListEntry.objects.get(rating="ML3")])
        self.good.save()

        regime_entry = RegimeEntry.objects.first()
        report_summary_prefix = ReportSummaryPrefix.objects.first()
        report_summary_subject = ReportSummarySubject.objects.first()
        data = [
            {
                "id": self.good_on_application.id,
                "control_list_entries": ["ML1"],
                "regime_entries": [regime_entry.id],
                "report_summary_prefix": report_summary_prefix.id,
                "report_summary_subject": report_summary_subject.id,
                "is_good_controlled": True,
                "comment": "some comment",
                "report_summary": "some string we expect to be overwritten",
                "is_ncsc_military_information_security": True,
            }
        ]
        response = self.client.put(self.assessment_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        good_on_application.refresh_from_db()
        all_cles = [cle.rating for cle in good_on_application.control_list_entries.all()]
        assert all_cles == ["ML1"]
        all_regime_entries = [regime_entry.id for regime_entry in good_on_application.regime_entries.all()]
        assert all_regime_entries == [regime_entry.id]
        assert good_on_application.report_summary_prefix_id == report_summary_prefix.id
        assert good_on_application.report_summary_subject_id == report_summary_subject.id
        assert good_on_application.is_good_controlled == True
        assert good_on_application.comment == "some comment"
        assert good_on_application.is_ncsc_military_information_security == True
        assert good_on_application.report_summary == f"{report_summary_prefix.name} {report_summary_subject.name}"
        assert good_on_application.assessed_by == self.gov_user
        assert good_on_application.assessment_date.isoformat() == "2023-11-03T12:00:00+00:00"

        good = good_on_application.good
        assert good.status == GoodStatus.VERIFIED
        assert [cle.rating for cle in good.control_list_entries.all()] == ["ML3", "ML1"]
        assert good_on_application.report_summary == f"{report_summary_prefix.name} {report_summary_subject.name}"
        assert good.report_summary_prefix_id == report_summary_prefix.id
        assert good.report_summary_subject_id == report_summary_subject.id

    @freeze_time("2023-11-03 12:00:00")
    def test_clear_assessments(self):
        good_on_application = self.good_on_application
        self.good.status = GoodStatus.VERIFIED
        self.good.control_list_entries.set([ControlListEntry.objects.get(rating="ML3")])
        self.good.save()

        data = [
            {
                "id": self.good_on_application.id,
                "control_list_entries": [],
                "regime_entries": [],
                "report_summary_prefix": None,
                "report_summary_subject": None,
                "is_good_controlled": None,
                "comment": None,
                "is_ncsc_military_information_security": None,
            }
        ]
        response = self.client.put(self.assessment_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        good_on_application.refresh_from_db()
        all_cles = [cle.rating for cle in good_on_application.control_list_entries.all()]
        assert all_cles == []
        all_regime_entries = [regime_entry.id for regime_entry in good_on_application.regime_entries.all()]
        assert all_regime_entries == []
        assert good_on_application.report_summary_prefix_id == None
        assert good_on_application.report_summary_subject_id == None
        assert good_on_application.is_good_controlled == None
        assert good_on_application.comment == None
        assert good_on_application.is_ncsc_military_information_security == None
        assert good_on_application.report_summary == None
        assert good_on_application.assessed_by == self.gov_user
        assert good_on_application.assessment_date.isoformat() == "2023-11-03T12:00:00+00:00"

    @freeze_time("2023-11-03 12:00:00")
    def test_valid_data_updates_multiple_records(self):
        good_on_application = self.good_on_application
        good_on_application_2 = self.good_on_application_2
        good_on_application_3 = self.good_on_application_3
        regime_entry = RegimeEntry.objects.first()
        report_summary_prefix = ReportSummaryPrefix.objects.first()
        report_summary_subject = ReportSummarySubject.objects.first()
        data = [
            {
                "id": self.good_on_application.id,
                "control_list_entries": ["ML1"],
                "regime_entries": [regime_entry.id],
                "report_summary_prefix": report_summary_prefix.id,
                "report_summary_subject": report_summary_subject.id,
                "is_good_controlled": True,
                "comment": "some comment",
                "report_summary": "some string we expect to be overwritten",
                "is_ncsc_military_information_security": True,
            },
            {
                "id": self.good_on_application_2.id,
                "control_list_entries": ["ML2"],
                "is_good_controlled": True,
                "comment": "some comment",
                "report_summary": "some report summary string",
                "is_ncsc_military_information_security": True,
            },
            {
                "id": self.good_on_application_3.id,
                "control_list_entries": [],
                "is_good_controlled": False,
                "comment": "some comment",
                "report_summary_subject": report_summary_subject.id,
                "report_summary": "some string we expect to be overwritten",
                "is_ncsc_military_information_security": True,
            },
        ]
        response = self.client.put(self.assessment_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        good_on_application.refresh_from_db()
        all_cles = [cle.rating for cle in good_on_application.control_list_entries.all()]
        assert all_cles == ["ML1"]
        all_regime_entries = [regime_entry.id for regime_entry in good_on_application.regime_entries.all()]
        assert all_regime_entries == [regime_entry.id]
        assert good_on_application.report_summary_prefix_id == report_summary_prefix.id
        assert good_on_application.report_summary_subject_id == report_summary_subject.id
        assert good_on_application.is_good_controlled == True
        assert good_on_application.comment == "some comment"
        assert good_on_application.is_ncsc_military_information_security == True
        assert good_on_application.report_summary == f"{report_summary_prefix.name} {report_summary_subject.name}"
        assert good_on_application.assessed_by == self.gov_user
        assert good_on_application.assessment_date.isoformat() == "2023-11-03T12:00:00+00:00"

        good_on_application_2.refresh_from_db()
        all_cles = [cle.rating for cle in good_on_application_2.control_list_entries.all()]
        assert all_cles == ["ML2"]
        assert good_on_application_2.report_summary_prefix_id == None
        assert good_on_application_2.report_summary_subject_id == None
        assert good_on_application_2.is_good_controlled == True
        assert good_on_application_2.comment == "some comment"
        assert good_on_application_2.is_ncsc_military_information_security == True
        assert good_on_application_2.report_summary == f"some report summary string"
        assert good_on_application_2.assessed_by == self.gov_user
        assert good_on_application_2.assessment_date.isoformat() == "2023-11-03T12:00:00+00:00"

        good_on_application_3.refresh_from_db()
        all_cles = [cle.rating for cle in good_on_application_3.control_list_entries.all()]
        assert all_cles == []
        assert good_on_application_3.report_summary_prefix_id == None
        assert good_on_application_3.report_summary_subject_id == None
        assert good_on_application_3.is_good_controlled == False
        assert good_on_application_3.comment == "some comment"
        assert good_on_application_3.is_ncsc_military_information_security == True
        assert good_on_application_3.report_summary == None
        assert good_on_application_3.assessed_by == self.gov_user
        assert good_on_application_3.assessment_date.isoformat() == "2023-11-03T12:00:00+00:00"

    def test_gov_authentication_enforced(self):
        response = self.client.put(self.assessment_url, [], **self.exporter_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_terminal_case_400(self):
        self.application.status = CaseStatus.objects.get(status="finalised")
        self.application.save()
        data = [
            {
                "id": self.good_on_application.id,
                "control_list_entries": ["ML1"],
                "is_good_controlled": True,
                "comment": "some comment",
                "report_summary": "some legacy summary",
                "is_ncsc_military_information_security": True,
            }
        ]
        response = self.client.put(self.assessment_url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_repeated_ids_400(self):
        data = [
            {
                "id": self.good_on_application.id,
                "control_list_entries": ["ML1"],
                "is_good_controlled": True,
                "comment": "some comment",
                "report_summary": "some legacy summary",
                "is_ncsc_military_information_security": True,
            },
            {
                "id": self.good_on_application.id,
                "control_list_entries": ["ML1"],
                "is_good_controlled": True,
                "comment": "some comment",
                "report_summary": "some legacy summary",
                "is_ncsc_military_information_security": True,
            },
        ]
        response = self.client.put(self.assessment_url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert response.json() == {
            "errors": [
                f"Multiple updates to a single GoodOnApplication id found. Duplicated ids; {self.good_on_application.id}"
            ]
        }
