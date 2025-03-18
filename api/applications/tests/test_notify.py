from unittest import mock

from django.test import override_settings

from api.applications import notify
from api.cases.enums import AdviceType, CountersignOrder
from api.cases.tests.factories import CountersignAdviceFactory, FinalAdviceFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.teams.enums import TeamIdEnum
from api.teams.models import Team
from gov_notify.enums import TemplateType
from gov_notify.payloads import CaseWorkerCountersignCaseReturn, ExporterCaseOpenedForEditing
from test_helpers.clients import DataTestClient


class NotifyTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        self.standard_application.refresh_from_db()

    @override_settings(EXPORTER_BASE_URL="https://exporter.lite.example.com")
    @mock.patch("api.applications.notify.send_email")
    def test_notify_licence_issued(self, mock_send_email):
        expected_payload = ExporterCaseOpenedForEditing(
            user_first_name=self.exporter_user.first_name,
            application_reference=self.standard_application.reference_code,
            exporter_frontend_url="https://exporter.lite.example.com/",
        )

        notify.notify_exporter_case_opened_for_editing(self.standard_application)

        mock_send_email.assert_called_with(
            self.exporter_user.email,
            TemplateType.EXPORTER_CASE_OPENED_FOR_EDITING,
            expected_payload,
        )

    @override_settings(CASEWORKER_BASE_URL="https://internal.lite.example.com")
    @mock.patch("api.applications.notify.send_email")
    def test_notify_countersign_case_returned(self, mock_send_email):
        self.gov_user.team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        self.gov_user.save()
        self.case.case_officer = self.gov_user
        self.case.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
        self.case._previous_status = CaseStatus.objects.get(status=CaseStatusEnum.FINAL_REVIEW_COUNTERSIGN)
        self.case.save()
        good_on_application = self.case.goods.first()
        advice = FinalAdviceFactory(
            user=self.gov_user,
            case=self.case,
            type=AdviceType.REFUSE,
            good=good_on_application.good,
        )
        countersign_advice = CountersignAdviceFactory(
            order=CountersignOrder.FIRST_COUNTERSIGN,
            valid=True,
            outcome_accepted=False,
            reasons="reasons",
            case=self.case,
            advice=advice,
        )
        frontend_url = f"https://internal.lite.example.com/cases/{self.case.id}/countersign-decision-advice/"
        data = {
            "case_reference": self.case.reference_code,
            "countersigned_user_name": f"{countersign_advice.countersigned_user.first_name} {countersign_advice.countersigned_user.last_name}",
            "countersign_reasons": countersign_advice.reasons,
            "recommendation_section_url": frontend_url,
        }
        expected_payload = CaseWorkerCountersignCaseReturn(**data)
        notify.notify_caseworker_countersign_return(self.case)

        mock_send_email.assert_called_with(
            self.gov_user.email,
            TemplateType.CASEWORKER_COUNTERSIGN_CASE_RETURN,
            expected_payload,
        )

    @mock.patch("api.applications.notify.send_email")
    def test_notify_countersign_case_returned_no_advice(self, mock_send_email):
        self.gov_user.team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        self.gov_user.save()
        self.case.case_officer = self.gov_user
        self.case.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
        self.case._previous_status = CaseStatus.objects.get(status=CaseStatusEnum.FINAL_REVIEW_COUNTERSIGN)
        self.case.save()
        notify.notify_caseworker_countersign_return(self.case)

        mock_send_email.assert_not_called()
