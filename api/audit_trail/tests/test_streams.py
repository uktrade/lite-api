from datetime import timedelta

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from api.audit_trail.streams.service import date_to_local_tz
from api.staticdata.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class AuditTrailStreamTestCase(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("audit_trail:streams", kwargs={"timestamp": 0})
        self.user = self.exporter_user

    def test_no_case_record_in_stream_with_no_audit(self):
        response = self.client.get(self.url, **self.exporter_headers)
        stream = response.json()

        self.assertEqual(0, len(stream["orderedItems"]))

    def test_status_audit_created_and_record(self):
        self.case = self.create_standard_application_case(self.organisation)

        response = self.client.get(self.url, **self.exporter_headers)
        stream = response.json()

        audit = Audit.objects.get(verb=AuditType.UPDATED_STATUS)
        self.assertEqual(2, len(stream["orderedItems"]))
        self.assertEqual(
            stream["orderedItems"][0],
            {
                "id": "dit:lite:case:change:status:{case_id}:{audit_id}:create".format(
                    case_id=self.case.id, audit_id=audit.id
                ),
                "object": {
                    "id": "dit:lite:case:change:status:{case_id}:{audit_id}".format(
                        case_id=self.case.id, audit_id=audit.id
                    ),
                    "attributedTo": {"id": "dit:lite:case:standard:{id}".format(id=self.case.id)},
                    "dit:to": {"dit:lite:case:status": CaseStatusEnum.SUBMITTED},
                    "dit:from": {"dit:lite:case:status": CaseStatusEnum.DRAFT},
                    "type": ["dit:lite:case:change", "dit:lite:activity", "dit:lite:case:change:status"],
                },
                "published": str(date_to_local_tz(audit.created_at)),
            },
        )
        self.assertEqual(
            stream["orderedItems"][1],
            {
                "id": "dit:lite:case:{case_type}:{id}:Update".format(
                    case_type=self.case.case_type.sub_type, id=self.case.id
                ),
                "object": {
                    "dit:caseOfficer": "",
                    "dit:countries": [],
                    "dit:status": self.case.status.status,
                    "dit:submittedDate": str(date_to_local_tz(self.case.submitted_at)),
                    "id": "dit:lite:case:{case_type}:{id}".format(
                        case_type=self.case.case_type.sub_type, id=self.case.id
                    ),
                    "type": [
                        "dit:lite:case",
                        "dit:lite:record",
                        "dit:lite:case:{case_type}".format(case_type=self.case.case_type.sub_type),
                    ],
                },
                "published": str(date_to_local_tz(audit.created_at)),
            },
        )

    @override_settings(STREAM_PAGE_SIZE=1)
    def test_duplicate_timestamp_appended(self):
        self.case = self.create_standard_application_case(self.organisation)

        now = timezone.now()
        Audit.objects.create(
            created_at=now - timedelta(days=1),
            actor=self.user,
            verb=AuditType.UPDATED_STATUS,
            target=self.case,
            payload={"status": {"new": "1", "old": "2"}},
        )
        Audit.objects.create(
            created_at=now,
            actor=self.user,
            verb=AuditType.UPDATED_STATUS,
            target=self.case,
            payload={"status": {"new": "3", "old": "1"}},
        )
        Audit.objects.create(
            created_at=now,
            actor=self.user,
            verb=AuditType.UPDATED_STATUS,
            target=self.case,
            payload={"status": {"new": "4", "old": "3"}},
        )

        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(len(response.json()["orderedItems"]), 1)

        next_response = self.client.get(response.json()["next"], **self.exporter_headers)

        self.assertEqual(len(next_response.json()["orderedItems"]), 2)  # Pulled in duplicate timestamp audit
