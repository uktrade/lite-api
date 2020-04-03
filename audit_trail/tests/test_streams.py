from django.urls import reverse

from audit_trail.models import Audit
from audit_trail.payload import AuditType
from audit_trail.service import create
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class AuditTrailStreamTestCase(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.user = self.exporter_user
        self.audit = create(actor=self.user, verb=AuditType.CREATED, action_object=self.case,)
        self.url = reverse("audit_trail:streams", kwargs={"n": 0})
        self.status_url = reverse("applications:manage_status", kwargs={"pk": self.case.id})

    def test_no_case_record_in_stream_with_no_audit(self):
        response = self.client.get(self.url, **self.exporter_headers)
        stream = response.json()

        self.assertEqual(0, len(stream["orderedItems"]))

    def test_status_audit_created_and_record(self):
        data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        old_status = self.case.status.status
        self.client.put(self.status_url, data=data, **self.exporter_headers)
        self.case.refresh_from_db()
        response = self.client.get(self.url, **self.exporter_headers)
        stream = response.json()

        audit = Audit.objects.get(verb=AuditType.UPDATED_STATUS.value)
        self.assertEqual(2, len(stream["orderedItems"]))
        self.assertEqual(
            stream["orderedItems"][0],
            {
                "id": "dit:lite:case:change:status:{case_id}:{audit_id}:update".format(
                    case_id=self.case.id, audit_id=audit.id
                ),
                "object": {
                    "attributedTo": {"id": "dit:lite:case:standard:{id}".format(id=self.case.id)},
                    "dit:to": {"dit:lite:case:status": CaseStatusEnum.get_text(data["status"])},
                    "dit:from": {"dit:lite:case:status": old_status},
                    "type": ["dit:lite:case:change", "dit:lite:activity", "dit:lite:case:change:status"],
                },
                "published": str(audit.created_at),
            },
        )
        self.assertEqual(
            stream["orderedItems"][1],
            {
                "id": "dit:lite:case:{case_type}:{id}:create".format(
                    case_type=self.case.case_type.sub_type, id=self.case.id
                ),
                "object": {
                    "dit:caseOfficer": "",
                    "dit:countries": [],
                    "dit:status": self.case.status.status,
                    "dit:submittedDate": str(self.case.submitted_at),
                    "id": "dit:lite:case:{case_type}:{id}".format(
                        case_type=self.case.case_type.sub_type, id=self.case.id
                    ),
                    "type": ["dit:lite:case", "dit:lite:record", "dit:lite:case:application"],
                },
                "published": str(audit.created_at),
            },
        )
