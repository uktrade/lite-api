from django.urls import reverse
from unittest import mock

from api.applications.serializers import good as serializers
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from test_helpers.clients import DataTestClient


class ApplicationGoodOnApplicationDocumentViewTests(DataTestClient):
    @mock.patch("api.documents.tasks.scan_document_for_viruses.now")
    @mock.patch("api.documents.libraries.s3_operations.upload_bytes_file")
    def test_audit_trail_create(self, upload_bytes_func, scan_document_func):
        application = self.create_draft_standard_application(organisation=self.organisation, user=self.exporter_user)
        good = self.create_good("A good", self.organisation)

        url = reverse(
            "applications:application-goods-documents",
            kwargs={
                "pk": application.pk,
                "good_pk": good.pk,
            },
        )

        data = {
            "name": "section5.png",
            "s3_key": "section5_20210223145814.png",
            "size": 1,
            "document_on_organisation": {
                "expiry_date": "2222-01-01",
                "reference_code": "1",
                "document_type": "section-five-certificate",
            },
        }

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, 201, response.json())

        audit = Audit.objects.get()

        self.assertEqual(audit.actor, self.exporter_user)
        self.assertEqual(audit.target.id, self.organisation.id)
        self.assertEqual(audit.verb, AuditType.DOCUMENT_ON_ORGANISATION_CREATE)
        self.assertEqual(audit.payload, {"file_name": "section5.png", "document_type": "section-five-certificate"})
