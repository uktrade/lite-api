from rest_framework import status

from django.urls import reverse

from test_helpers.clients import DataTestClient

from api.audit_trail.models import (
    Audit,
    AuditType,
)
from api.appeals.models import AppealDocument
from api.appeals.tests.factories import AppealFactory
from api.queues.models import Queue

from lite_routing.routing_rules_internal.enums import QueuesEnum


class AppealApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.application = self.create_standard_application_case(self.organisation)
        self.case = self.application.get_case()

        # We don't care about audit objects created by the above method call so
        # we reset them to a known state
        Audit.objects.all().delete()

    def test_create_appeal_standard_application(self):
        self.assertIsNone(self.application.appeal)

        url = reverse(
            "applications:appeals",
            kwargs={"pk": self.application.id},
        )
        response = self.client.post(
            url,
            {"grounds_for_appeal": "These are the grounds for appeal"},
            **self.exporter_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.application.refresh_from_db()
        self.assertIsNotNone(self.application.appeal)

        appeal = self.application.appeal
        self.assertEqual(
            appeal.grounds_for_appeal,
            "These are the grounds for appeal",
        )
        self.assertQuerysetEqual(
            appeal.documents.all(),
            AppealDocument.objects.none(),
        )

        self.assertIn(
            Queue.objects.get(id=QueuesEnum.LU_APPEALS),
            self.application.queues.all(),
        )

        audit_events = Audit.objects.order_by("created_at")

        appeal_event = audit_events[0]
        self.assertEqual(appeal_event.verb, AuditType.EXPORTER_APPEALED_REFUSAL)
        self.assertEqual(appeal_event.actor, self.exporter_user)
        self.assertEqual(appeal_event.target, self.case)
        self.assertEqual(
            appeal_event.payload,
            {},
        )

        move_case_event = audit_events[1]
        self.assertEqual(move_case_event.verb, AuditType.MOVE_CASE)
        self.assertEqual(move_case_event.actor, self.system_user)
        self.assertEqual(move_case_event.target, self.case)
        self.assertEqual(
            move_case_event.payload,
            {
                "case_status": "submitted",
                "queue_ids": [QueuesEnum.LU_APPEALS],
                "queues": ["Licensing Unit Appeals"],
            },
        )

        self.assertEqual(
            response.json(),
            {
                "id": str(appeal.pk),
                "documents": [],
                "grounds_for_appeal": appeal.grounds_for_appeal,
            },
        )

    def test_create_appeal_invalid_application_pk(self):
        url = reverse(
            "applications:appeals",
            kwargs={"pk": "4ec19e01-71ec-40fc-83c1-442c2706868d"},
        )
        response = self.client.post(
            url,
            {"grounds_for_appeal": "These are the grounds for appeal"},
            **self.exporter_headers,
        )
        self.assertEqual(response.status_code, 404)

    def test_get_appeal(self):
        appeal = AppealFactory()
        url = reverse(
            "applications:appeal",
            kwargs={"pk": self.application.pk, "appeal_pk": appeal.pk},
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.json(),
            {
                "id": str(appeal.pk),
                "documents": [],
                "grounds_for_appeal": appeal.grounds_for_appeal,
            },
        )

    def test_get_appeal_invalid_application_pk(self):
        appeal = AppealFactory()
        url = reverse(
            "applications:appeal",
            kwargs={
                "pk": "4ec19e01-71ec-40fc-83c1-442c2706868d",
                "appeal_pk": appeal.pk,
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_get_appeal_invalid_appeal_pk(self):
        appeal = AppealFactory()
        url = reverse(
            "applications:appeal",
            kwargs={
                "pk": self.application.pk,
                "appeal_pk": "4ec19e01-71ec-40fc-83c1-442c2706868d",
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
