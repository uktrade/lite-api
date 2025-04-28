import concurrent.futures
import pytest

from unittest import mock
from uuid import UUID

from parameterized import parameterized

from django.test import TransactionTestCase

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer
from api.applications.application_manifest import StandardApplicationManifest
from api.applications.tests.factories import StandardApplicationFactory
from api.cases.models import (
    BadSubStatus,
    Case,
    LicenceDecision,
)
from api.cases.enums import (
    AdviceType,
    CaseTypeSubTypeEnum,
)
from api.cases.tests.factories import (
    CaseFactory,
    CaseTypeFactory,
)
from api.f680.application_manifest import F680ApplicationManifest
from api.f680.tests.factories import SubmittedF680ApplicationFactory
from api.licences.enums import LicenceStatus
from api.licences.tests.factories import StandardLicenceFactory
from api.staticdata.decisions.models import Decision
from api.staticdata.statuses.enums import (
    CaseStatusEnum,
    CaseSubStatusIdEnum,
)
from api.staticdata.statuses.factories import (
    CaseStatusFactory,
    CaseSubStatusFactory,
)
from api.staticdata.statuses.models import (
    CaseStatus,
    CaseSubStatus,
)
from api.users.enums import SystemUser
from api.users.models import (
    BaseUser,
    ExporterUser,
)
from api.users.tests.factories import (
    ExporterUserFactory,
    GovUserFactory,
    RoleFactory,
)
from test_helpers.clients import DataTestClient


class CaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(application)

    def test_set_sub_status_invalid(self):
        self.assertRaises(BadSubStatus, self.case.set_sub_status, CaseSubStatusIdEnum.FINALISED__APPROVED)

    def test_superseded_by_amendment_exists(self):
        exporter_user = ExporterUser.objects.first()
        amendment = self.case.create_amendment(exporter_user)
        assert self.case.superseded_by == amendment.case_ptr

    def test_superseded_by_no_amendment_exists(self):
        assert self.case.superseded_by == None

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

        # Check sub status audit
        audit = Audit.objects.filter(verb=AuditType.UPDATED_SUB_STATUS).order_by("-created_at")[0]
        sub_status_name = self.case.sub_status.name
        case_status_name = CaseStatusEnum.get_text(status)
        self.assertEqual(
            audit.payload,
            {"status": case_status_name, "sub_status": sub_status_name},
        )
        audit_text = AuditSerializer(audit).data["text"]
        self.assertEqual(audit_text, f"updated the status to {case_status_name} - {sub_status_name}")

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

    def test_case_save_reset_sub_status_system_audit(self):
        sub_status = CaseSubStatus.objects.get(id=UUID(CaseSubStatusIdEnum.UNDER_FINAL_REVIEW__INFORM_LETTER_SENT))
        case = CaseFactory(
            status=CaseStatus.objects.get(status="under_final_review"),
            sub_status=sub_status,
        )
        case.refresh_from_db()
        assert case.sub_status == sub_status
        case.status = CaseStatus.objects.get(status="finalised")
        case.save()
        case.refresh_from_db()
        self.assertEqual(case.sub_status_id, None)
        # Check add audit
        audit = Audit.objects.get(verb=AuditType.UPDATED_SUB_STATUS)
        self.assertEqual(
            audit.payload,
            {"status": "Finalised", "sub_status": None},
        )
        audit_text = AuditSerializer(audit).data["text"]
        self.assertEqual(audit_text, "updated the status to Finalised")

    def test_change_status_same_status(self):
        status = CaseStatus.objects.get(status="submitted")
        app = StandardApplicationFactory(
            status=status,
        )
        case = app.get_case()
        case.change_status(self.gov_user, status=status)
        case.refresh_from_db()
        assert case.status == status

    @mock.patch("api.licences.helpers.update_licence_status")
    @mock.patch("lite_routing.routing_rules_internal.routing_engine.run_routing_rules")
    def test_change_status_new_status(self, mock_run_routing_rules, mock_update_licence_status):
        original_status = CaseStatus.objects.get(status="submitted")
        new_status = CaseStatus.objects.get(status="ogd_advice")
        app = StandardApplicationFactory(
            status=original_status,
        )
        case = app.get_case()
        case.change_status(self.gov_user, status=new_status, note="some note")
        case.refresh_from_db()
        assert case.status == new_status
        audit_entry = Audit.objects.first()
        assert audit_entry.verb == AuditType.UPDATED_STATUS
        assert audit_entry.target == case
        assert audit_entry.payload == {
            "status": {"new": new_status.status, "old": original_status.status},
            "additional_text": "some note",
        }
        assert audit_entry.actor == self.gov_user
        mock_update_licence_status.assert_called_with(case, new_status.status)
        mock_run_routing_rules.assert_called_with(case=case, keep_status=True)

    @mock.patch("api.applications.notify.notify_exporter_case_opened_for_editing")
    def test_change_status_to_applicant_editing(self, mock_notify_exporter_case_opened_for_editing):
        original_status = CaseStatus.objects.get(status="submitted")
        new_status = CaseStatus.objects.get(status="applicant_editing")
        app = StandardApplicationFactory(
            status=original_status,
        )
        case = app.get_case()
        case.change_status(self.gov_user, status=new_status, note="some note")
        case.refresh_from_db()
        assert case.status == new_status
        mock_notify_exporter_case_opened_for_editing.assert_called_with(case)

    @parameterized.expand(
        [
            (CaseStatusEnum.WITHDRAWN,),
            (CaseStatusEnum.CLOSED,),
        ]
    )
    @mock.patch("api.cases.libraries.finalise.remove_flags_on_finalisation")
    @mock.patch("api.cases.libraries.finalise.remove_flags_from_audit_trail")
    def test_change_status_to_closed(
        self, case_status, mock_remove_flags_from_audit_trail, mock_remove_flags_on_finalisation
    ):
        original_status = CaseStatus.objects.get(status="submitted")
        new_status = CaseStatus.objects.get(status=case_status)
        app = StandardApplicationFactory(
            status=original_status,
        )
        case = app.get_case()
        case.change_status(self.gov_user, status=new_status, note="some note")
        case.refresh_from_db()
        assert case.status == new_status
        mock_remove_flags_from_audit_trail.assert_called_with(case)
        mock_remove_flags_on_finalisation.assert_called_with(case)

    @parameterized.expand(
        [
            (StandardApplicationFactory, StandardApplicationManifest),
            (SubmittedF680ApplicationFactory, F680ApplicationManifest),
        ]
    )
    def test_get_application_manifest(self, create_application, expected_manifest_class):
        application = create_application()
        case = Case.objects.get(id=application.id)
        manifest = case.get_application_manifest()
        assert manifest.__class__ == expected_manifest_class

    @parameterized.expand(
        [
            (StandardApplicationFactory,),
            (SubmittedF680ApplicationFactory,),
        ]
    )
    def test_get_application(self, create_application):
        application = create_application()
        case = Case.objects.get(id=application.id)
        retrieved_application = case.get_application()
        assert retrieved_application == application


@pytest.mark.requires_transactions
class CaseRaceConditionTests(TransactionTestCase):
    def setUp(self):
        super().setUp()

        BaseUser.objects.get_or_create(
            id=SystemUser.id,
            defaults={
                "email": "lite@example.com",  # /PS-IGNORE
            },
        )
        RoleFactory(id="00000000-0000-0000-0000-000000000001")

        Decision.objects.get_or_create(name=AdviceType.APPROVE)

        self.case_type = CaseTypeFactory(sub_type=CaseTypeSubTypeEnum.STANDARD)

        self.draft_case_status = CaseStatusFactory(status=CaseStatusEnum.DRAFT)
        self.under_final_review_case_status = CaseStatusFactory(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
        self.finalised_case_status = CaseStatusFactory(status=CaseStatusEnum.FINALISED)

        self.exporter_user = ExporterUserFactory()
        self.gov_user = GovUserFactory()

        self.finalised_approved_sub_status = CaseSubStatusFactory(
            id=CaseSubStatusIdEnum.FINALISED__APPROVED,
            name="Finalised - Approved",
            parent_status=self.finalised_case_status,
        )
        self.finalised_refused_sub_status = CaseSubStatusFactory(
            id=CaseSubStatusIdEnum.FINALISED__REFUSED,
            name="Finalised - Refused",
            parent_status=self.finalised_case_status,
        )

    def test_finalise_approved_case_race_condition(self):
        case = CaseFactory(
            case_type=self.case_type,
            status=self.under_final_review_case_status,
            submitted_by=self.exporter_user,
        )
        original_case = Case.objects.get(pk=case.pk)
        same_case = Case.objects.get(pk=case.pk)

        licence = StandardLicenceFactory(
            case=case,
            status=LicenceStatus.DRAFT,
        )

        def _finalise(case):
            return case.finalise(self.gov_user, {AdviceType.APPROVE}, "Note")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_1 = executor.submit(_finalise, original_case)
            future_2 = executor.submit(_finalise, same_case)

            licence_id_1 = future_1.result()
            licence_id_2 = future_2.result()

        original_case.refresh_from_db()
        self.assertEqual(original_case.status, self.finalised_case_status)
        self.assertEqual(
            LicenceDecision.objects.count(),
            1,
        )
        self.assertEqual(licence_id_1, licence.pk)
        self.assertEqual(licence_id_2, licence.pk)

    def test_finalise_refused_case_race_condition(self):
        case = CaseFactory(
            case_type=self.case_type,
            status=self.under_final_review_case_status,
            submitted_by=self.exporter_user,
        )

        original_case = Case.objects.get(pk=case.pk)
        same_case = Case.objects.get(pk=case.pk)

        def _finalise(case):
            return case.finalise(self.gov_user, {AdviceType.REFUSE}, "Note")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_1 = executor.submit(_finalise, original_case)
            future_2 = executor.submit(_finalise, same_case)

            licence_id_1 = future_1.result()
            licence_id_2 = future_2.result()

        original_case.refresh_from_db()
        self.assertEqual(original_case.status, self.finalised_case_status)
        self.assertEqual(
            LicenceDecision.objects.count(),
            1,
        )
        self.assertEqual(licence_id_1, "")
        self.assertEqual(licence_id_2, "")
