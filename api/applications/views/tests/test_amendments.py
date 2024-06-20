from unittest import mock
from django.urls import reverse
from rest_framework import status

from api.applications import models as application_models
from api.applications.models import StandardApplication
from api.applications.tests.factories import StandardApplicationFactory, GoodOnApplicationFactory
from api.organisations.tests.factories import OrganisationFactory

from test_helpers.clients import DataTestClient


class TestCreateApplicationAmendment(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = StandardApplicationFactory(organisation=self.organisation)
        self.good_on_application = GoodOnApplicationFactory(application=self.application)
        self.url = reverse(
            "applications:create_amendment",
            kwargs={
                "pk": str(self.application.pk),
            },
        )

    def test_create_amendment(self):
        response = self.client.post(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        amendment_id = response.json().get("id")
        amendment_application = StandardApplication.objects.get(id=amendment_id)
        self.assertEqual(amendment_application.name, self.application.name)
        self.assertEqual(amendment_application.amendment_of_id, self.application.id)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, "superseded_by_exporter_edit")

    @mock.patch.object(application_models.GoodOnApplication, "clone")
    def test_create_amendment_partial_failure(self, mocked_good_on_application_clone):
        self.assertEqual(list(StandardApplication.objects.all()), [self.application])
        mocked_good_on_application_clone.side_effect = Exception
        with self.assertRaises(Exception):
            response = self.client.post(self.url, **self.exporter_headers)
        self.assertEqual(list(StandardApplication.objects.all()), [self.application])

    def test_create_amendment_exporter_wrong_organisation(self):
        self.application.organisation = OrganisationFactory()
        self.application.save()
        response = self.client.post(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_amendment_application_does_not_exist(self):
        self.application.delete()
        response = self.client.post(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
