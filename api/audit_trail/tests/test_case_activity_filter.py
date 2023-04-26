from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.audit_trail.tests.factories import AuditFactory
from api.cases.models import Case
from api.teams.tests.factories import TeamFactory
from test_helpers.clients import DataTestClient
from api.users.enums import UserType
from api.users.models import GovUser
from api.users.tests.factories import GovUserFactory, ExporterUserFactory
from api.audit_trail.service import filter_object_activity


class CasesAuditTrailSearchTestCase(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.team = TeamFactory()
        self.gov_user = GovUserFactory(team=self.team)
        self.exporter_user = ExporterUserFactory()
        self.content_type = ContentType.objects.get_for_model(Case)

    def test_filter_by_gov_user(self):
        AuditFactory(actor=self.gov_user, target=self.case.get_case())

        res = filter_object_activity(
            object_id=self.case.id, object_content_type=self.content_type, user_id=self.gov_user.pk
        )
        self.assertEqual(res.count(), 1)
        self.assertEqual(res.first().actor_object_id, str(self.gov_user.pk))

    def test_filter_by_exporter_user(self):
        AuditFactory(actor=self.exporter_user, target=self.case.get_case())

        res = filter_object_activity(
            object_id=self.case.id, object_content_type=self.content_type, user_id=self.exporter_user.pk
        )
        self.assertEqual(res.count(), 1)
        self.assertEqual(res.first().actor_object_id, str(self.exporter_user.pk))

    def test_filter_by_team(self):
        AuditFactory(actor=self.gov_user, target=self.case.get_case())

        res = filter_object_activity(object_id=self.case.id, object_content_type=self.content_type, team=self.team)

        self.assertEqual(res.count(), 1)
        self.assertEqual(res.first().actor_object_id, str(self.gov_user.pk))

        # Create new gov user on another team and test again
        fake_team = TeamFactory()
        fake_user = GovUserFactory(team=fake_team)
        AuditFactory(actor=fake_user, target=self.case.get_case())

        self.assertNotEqual(fake_team.id, self.team.id)
        self.assertNotEqual(fake_user.pk, self.gov_user.pk)

        res = filter_object_activity(object_id=self.case.id, object_content_type=self.content_type, team=self.team)

        self.assertEqual(res.count(), 1)
        self.assertEqual(res.first().actor_object_id, str(self.gov_user.pk))

    def test_filter_by_audit_type(self):
        audit_type = AuditType.CREATED
        fake_audit_type = AuditType.CREATED_CASE_NOTE
        AuditFactory(actor=self.exporter_user, verb=audit_type, target=self.case.get_case())
        AuditFactory(actor=self.gov_user, verb=fake_audit_type, target=self.case.get_case())

        res = filter_object_activity(
            object_id=self.case.id, object_content_type=self.content_type, audit_type=audit_type
        )

        self.assertEqual(res.count(), 1)
        self.assertEqual(res.first().actor_object_id, str(self.exporter_user.pk))
        self.assertEqual(res.first().verb, audit_type)

    def test_filter_by_user_type(self):
        AuditFactory(actor=self.gov_user, target=self.case.get_case())
        AuditFactory(actor=self.exporter_user, target=self.case.get_case())

        # check gov filter
        res = filter_object_activity(
            object_id=self.case.id, object_content_type=self.content_type, user_type=UserType.INTERNAL
        )

        self.assertEqual(res.count(), 1)
        self.assertEqual(res.first().actor_object_id, str(self.gov_user.pk))

        # check exporter filter
        res = filter_object_activity(
            object_id=self.case.id, object_content_type=self.content_type, user_type=UserType.EXPORTER
        )
        self.assertEqual(res.count(), 2)
        self.assertEqual(res.first().actor_object_id, str(self.exporter_user.pk))

    def test_filter_by_dates(self):
        start_date = timezone.now()
        middle_date = start_date + timedelta(days=3)
        end_date = start_date + timedelta(days=5)

        AuditFactory(created_at=start_date, actor=self.gov_user, target=self.case.get_case())
        AuditFactory(created_at=middle_date, actor=self.gov_user, target=self.case.get_case())
        AuditFactory(created_at=end_date, actor=self.gov_user, target=self.case.get_case())

        res = filter_object_activity(
            object_id=self.case.id, object_content_type=self.content_type, date_from=start_date.date()
        )

        self.assertEqual(res.count(), 4)

        res = filter_object_activity(
            object_id=self.case.id, object_content_type=self.content_type, date_from=middle_date.date()
        )

        self.assertEqual(res.count(), 2)

        res = filter_object_activity(
            object_id=self.case.id, object_content_type=self.content_type, date_from=end_date.date()
        )

        self.assertEqual(res.count(), 1)

        res = filter_object_activity(
            object_id=self.case.id,
            object_content_type=self.content_type,
            date_from=start_date.date(),
            date_to=middle_date.date(),
        )

        self.assertEqual(res.count(), 3)

        res = filter_object_activity(
            object_id=self.case.id,
            object_content_type=self.content_type,
            date_from=middle_date.date(),
            date_to=end_date.date(),
        )

        self.assertEqual(res.count(), 2)

        res = filter_object_activity(
            object_id=self.case.id,
            object_content_type=self.content_type,
            date_from=end_date.date(),
            date_to=end_date.date(),
        )

        self.assertEqual(res.count(), 1)

        after_end_date = end_date + timedelta(days=1)
        before_start_date = start_date - timedelta(days=1)

        res = filter_object_activity(
            object_id=self.case.id, object_content_type=self.content_type, date_from=after_end_date.date()
        )

        self.assertEqual(res.count(), 0)

        res = filter_object_activity(
            object_id=self.case.id, object_content_type=self.content_type, date_to=before_start_date.date()
        )

        self.assertEqual(res.count(), 0)
