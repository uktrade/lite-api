from audit_trail import service
from audit_trail.models import Audit
from audit_trail.payload import AuditType
from audit_trail.streams.exceptions import PayloadSchemaException, AuditSchemaException
from audit_trail.streams.schemas.payloads import VERB_SCHEMAS
from test_helpers.clients import DataTestClient


class AuditTrailPayloadSchemaTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)

    def test_update_status_valid_payload_schema_success(self):
        audit_qs = Audit.objects.all()

        self.assertEqual(audit_qs.count(), 0)

        service.create(
            actor=self.exporter_user,
            verb=AuditType.UPDATED_STATUS,
            target=self.case.get_case(),
            payload={
                "status": {"new": "submitted", "old": "draft"}
            }
        )

        self.assertEqual(audit_qs.count(), 1)

    def test_update_status_invalid_payload_schema_fail(self):
        audit_qs = Audit.objects.all()
        invalid_payload = {"status": {"newa": "submitted", "old": "draft"}}

        self.assertEqual(audit_qs.count(), 0)

        with self.assertRaises(PayloadSchemaException) as e:
            service.create(
                actor=self.exporter_user,
                verb=AuditType.UPDATED_STATUS,
                target=self.case.get_case(),
                payload=invalid_payload
            )

        self.assertEqual(audit_qs.count(), 0)
        self.assertEqual(e.exception.message, {
            "schema": VERB_SCHEMAS[AuditType.UPDATED_STATUS],
            "data": invalid_payload
        })


class AuditTrailObjectSchemaTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)

    def test_update_status_valid_object_schema_success(self):
        audit_qs = Audit.objects.all()

        self.assertEqual(audit_qs.count(), 0)

        service.create(
            actor=self.exporter_user,
            verb=AuditType.UPDATED_STATUS,
            target=self.case.get_case(),
            payload={
                "status": {"new": "submitted", "old": "draft"}
            }
        )

        self.assertEqual(audit_qs.count(), 1)

    def test_update_status_invalid_object_schema_fail(self):
        audit_qs = Audit.objects.all()

        self.assertEqual(audit_qs.count(), 0)

        with self.assertRaises(AuditSchemaException):
            service.create(
                actor=self.exporter_user,
                verb=AuditType.UPDATED_STATUS,
                target=self.case,
                payload={
                    "status": {"new": "submitted", "old": "draft"}
                }
            )

        self.assertEqual(audit_qs.count(), 0)
