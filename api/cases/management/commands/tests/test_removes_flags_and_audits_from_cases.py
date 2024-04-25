from django.core.management import call_command
from parameterized import parameterized

from test_helpers.clients import DataTestClient

from api.flags.models import Flag
from api.users.models import BaseUser
from api.users.enums import UserType
from api.audit_trail.enums import AuditType

from api.audit_trail import service as audit_trail_service

from api.cases.tests.factories import FinalAdviceFactory
from api.cases.enums import AdviceType
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.audit_trail.models import Audit


class TestCommand(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application_case(self.organisation)
        self.original_flag_id = self.application.flags.first().id

        # Add Flag to test with removal after Finalise
        self.test_flag = Flag.objects.all().first()
        self.test_flag.remove_on_finalised = True
        self.test_flag.save()
        self.application.flags.add(self.test_flag)

        user = BaseUser(email="test@mail.com", first_name="John", last_name="Smith", type=UserType.SYSTEM)

        self.case = self.application.get_case()

        self.test_audit = audit_trail_service.create(
            actor=user,
            verb=AuditType.ADD_FLAGS,
            target=self.case,
            payload={
                "added_flags": [self.test_flag.name],
                "additional_text": "test",
                "added_flags_id": [str(self.test_flag.id)],
            },
        )

        FinalAdviceFactory(user=self.gov_user, case=self.application, type=AdviceType.APPROVE)

    @parameterized.expand(
        case_status for case_status in [CaseStatusEnum.FINALISED, CaseStatusEnum.WITHDRAWN, CaseStatusEnum.CLOSED]
    )
    def test_call_command_removes_flags_and_audits_from_cases(self, case_status):
        status_var = CaseStatus.objects.get(status=case_status)
        self.case.status = status_var
        self.case.save()

        audit_queryset = Audit.objects.filter(target_object_id=self.case.id)

        self.assertEqual(self.case.flags.count(), 2)
        self.assertEqual(audit_queryset.count(), 2)

        call_command("removes_flags_and_audits_from_cases")

        audit_queryset = Audit.objects.filter(target_object_id=self.case.id)

        self.assertNotIn(self.test_flag, self.case.flags.all())
        self.assertEqual(audit_queryset.count(), 1)
        self.assertNotIn(self.test_audit, audit_queryset)
