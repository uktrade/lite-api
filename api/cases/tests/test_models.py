from uuid import UUID
from parameterized import parameterized

from api.cases.models import Case, BadSubStatus
from api.cases.tests.factories import CaseFactory
from api.staticdata.statuses.enums import CaseSubStatusIdEnum
from api.staticdata.statuses.models import CaseStatus, CaseSubStatus
from test_helpers.clients import DataTestClient


class CaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(application)

    def test_set_sub_status_invalid(self):
        self.assertRaises(BadSubStatus, self.case.set_sub_status, CaseSubStatusIdEnum.FINALISED__APPROVED)

    @parameterized.expand(
        [
            ("finalised", CaseSubStatusIdEnum.FINALISED__APPROVED),
            ("finalised", CaseSubStatusIdEnum.FINALISED__REFUSED),
            ("under_final_review", CaseSubStatusIdEnum.UNDER_FINAL_REVIEW__INFORM_LETTER_SENT),
        ]
    )
    def test_set_sub_status(self, status, sub_status):
        self.case.status = CaseStatus.objects.get(status=status)
        self.case.save()
        self.case.set_sub_status(sub_status)

        self.case.refresh_from_db()
        assert str(self.case.sub_status.id) == sub_status

    @parameterized.expand(
        [
            (
                "under_final_review",
                "under_final_review",
                UUID(CaseSubStatusIdEnum.UNDER_FINAL_REVIEW__INFORM_LETTER_SENT),
                UUID(CaseSubStatusIdEnum.UNDER_FINAL_REVIEW__INFORM_LETTER_SENT),
            ),
            ("under_final_review", "finalised", UUID(CaseSubStatusIdEnum.UNDER_FINAL_REVIEW__INFORM_LETTER_SENT), None),
        ]
    )
    def test_case_save_reset_sub_status(self, previous_status, new_status, previous_sub_status, expected_sub_status):
        sub_status = CaseSubStatus.objects.get(id=previous_sub_status)
        case = CaseFactory(
            status=CaseStatus.objects.get(status=previous_status),
            sub_status=sub_status,
        )
        case.refresh_from_db()
        assert case.sub_status == sub_status
        case.status = CaseStatus.objects.get(status=new_status)
        case.save()
        case.refresh_from_db()
        self.assertEqual(case.sub_status_id, expected_sub_status)
