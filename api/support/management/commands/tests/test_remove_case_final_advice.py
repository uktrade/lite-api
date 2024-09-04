from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
import pytest

from django.core.management import call_command, CommandError

from api.applications.tests.factories import AdviceFactory, FinalAdviceOnApplicationFactory
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import AdviceLevel
from api.staticdata.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class RemoveCaseFinalAdviceMgmtCommandTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = FinalAdviceOnApplicationFactory()
        self.application.advice.set([AdviceFactory(level=AdviceLevel.USER)])

    def test_remove_case_final_advice_command(self):

        self.application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        self.application.save()

        self.assertEqual(self.application.advice.filter(level=AdviceLevel.FINAL).exists(), True)
        self.assertEqual(self.application.advice.all().count(), 2)

        call_command("remove_case_final_advice", case_reference=self.application.reference_code)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, CaseStatusEnum.UNDER_FINAL_REVIEW)
        self.assertEqual(self.application.advice.filter(level=AdviceLevel.FINAL).exists(), False)
        self.assertEqual(self.application.advice.all().count(), 1)

        audit_dev = Audit.objects.get(verb=AuditType.DEVELOPER_INTERVENTION)
        self.assertEqual(audit_dev.actor, self.system_user)
        self.assertEqual(audit_dev.target.id, self.application.id)

        self.assertEqual(
            audit_dev.payload,
            {
                "additional_text": "Removed final advice.",
            },
        )

        audit = Audit.objects.get(verb=AuditType.UPDATED_STATUS)
        self.assertEqual(audit.actor, self.system_user)
        self.assertEqual(audit.target.id, self.application.id)

        self.assertEqual(
            audit.payload,
            {
                "status": {"new": self.application.status.status, "old": CaseStatusEnum.SUBMITTED},
                "additional_text": "",
            },
        )

    def test_remove_case_final_advice_command_status_not_updated(self):

        call_command("remove_case_final_advice", case_reference=self.application.reference_code)

        self.assertEqual(Audit.objects.filter(verb=AuditType.UPDATED_STATUS).exists(), False)

    def test_remove_case_status_change_command_dry_run(self):

        self.assertEqual(self.application.advice.filter(level=AdviceLevel.FINAL).exists(), True)
        self.assertEqual(self.application.advice.all().count(), 2)

        call_command("remove_case_final_advice", "--dry_run", case_reference=self.application.reference_code)

        self.application.refresh_from_db()
        self.assertEqual(self.application.advice.filter(level=AdviceLevel.FINAL).exists(), True)
        self.assertEqual(self.application.advice.all().count(), 2)
        self.assertEqual(Audit.objects.filter(verb=AuditType.DEVELOPER_INTERVENTION).exists(), False)

    def test_remove_case_final_advice_command_no_final_advise(self):

        self.application.advice.filter(level=AdviceLevel.FINAL).delete()
        with pytest.raises(CommandError):
            call_command("remove_case_final_advice", case_reference=self.application.reference_code)

    def test_remove_case_final_advice_command_missing_case_ref(self):

        self.application.advice.filter(level=AdviceLevel.FINAL).delete()
        self.assertEqual(self.application.advice.all().count(), 1)

        with pytest.raises(CommandError):
            call_command("remove_case_final_advice", case_reference="bad-ref")

        self.assertEqual(self.application.advice.all().count(), 1)
