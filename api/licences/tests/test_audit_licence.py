import django.utils.timezone

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.licences.models import Licence
from api.licences.enums import LicenceStatus
from test_helpers.clients import DataTestClient


class AuditLicenceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)

    def test_create_new_licence(self):
        licence = Licence.objects.create(
            case=self.standard_application,
            status=LicenceStatus.ISSUED,
            reference_code="test_reference",
            start_date=django.utils.timezone.now().date(),
            duration=10,
        )

        audit_records = Audit.objects.filter(verb=AuditType.LICENCE_UPDATED_STATUS)

        self.assertEqual(audit_records.count(), 1)
        self.assertEqual(audit_records[0].action_object, licence)
        self.assertEqual(audit_records[0].target, self.standard_application.get_case())
        self.assertEqual(audit_records[0].payload["licence"], "test_reference")
        self.assertEqual(audit_records[0].payload["status"], "issued")

    def test_update_existing_licence(self):
        licence = Licence.objects.create(
            case=self.standard_application,
            status=LicenceStatus.ISSUED,
            reference_code="test_reference",
            start_date=django.utils.timezone.now().date(),
            duration=10,
        )
        licence.status = LicenceStatus.REVOKED
        licence.save()

        audit_records = Audit.objects.filter(verb=AuditType.LICENCE_UPDATED_STATUS).order_by("created_at")

        self.assertEqual(audit_records.count(), 2)
        self.assertEqual(audit_records[0].payload["status"], "issued")
        self.assertEqual(audit_records[1].payload["status"], "revoked")

    def test_update_existing_licence_no_change(self):
        licence = Licence(
            case=self.standard_application,
            status=LicenceStatus.ISSUED,
            reference_code="test_reference",
            start_date=django.utils.timezone.now().date(),
            duration=10,
        )
        licence.save()
        licence.status = LicenceStatus.ISSUED
        licence.save()

        audit_records = Audit.objects.filter(verb=AuditType.LICENCE_UPDATED_STATUS)

        self.assertEqual(audit_records.count(), 1)
        self.assertEqual(audit_records[0].payload["status"], "issued")
