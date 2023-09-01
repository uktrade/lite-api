from rest_framework import status

from django.urls import reverse

from test_helpers.clients import DataTestClient

from api.appeals.models import AppealDocument
from api.appeals.tests.factories import AppealFactory
from api.queues.models import Queue

from lite_routing.routing_rules_internal.enums import QueuesEnum


class AppealApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.application = self.create_standard_application_case(self.organisation)

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
