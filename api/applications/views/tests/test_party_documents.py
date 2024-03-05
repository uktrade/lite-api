from moto import mock_aws
from parameterized import parameterized

from django.http import FileResponse
from django.urls import reverse
from rest_framework import status

from api.applications.tests.factories import PartyOnApplicationFactory, StandardApplicationFactory
from api.parties.tests.factories import PartyFactory, PartyDocumentFactory
from test_helpers.clients import DataTestClient


@mock_aws
class PartyDocumentStreamTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.party = PartyFactory(
            organisation=self.organisation,
        )
        self.party_on_application = PartyOnApplicationFactory(party=self.party)
        self.application = self.party_on_application.application
        self.create_default_bucket()
        self.put_object_in_default_bucket("thisisakey", b"test")

    def test_get_party_document_stream(self):
        party_document = PartyDocumentFactory(
            party=self.party,
            s3_key="thisisakey",
            name="doc1.pdf",
            safe=True,
        )

        url = reverse(
            "applications:party_document_stream",
            kwargs={
                "pk": str(self.application.pk),
                "party_pk": str(self.party.pk),
                "document_pk": str(party_document.pk),
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response, FileResponse)
        self.assertEqual(b"".join(response.streaming_content), b"test")

    def test_get_party_document_stream_invalid_document_pk(self):
        another_party = PartyFactory(
            organisation=self.organisation,
        )
        party_document = PartyDocumentFactory(
            party=self.party,
            s3_key="thisisakey",
            name="doc1.pdf",
            safe=True,
        )

        url = reverse(
            "applications:party_document_stream",
            kwargs={
                "pk": str(self.application.pk),
                "party_pk": str(another_party.pk),
                "document_pk": str(party_document.pk),
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_party_document_stream_invalid_application_pk(self):
        another_application = StandardApplicationFactory()
        party_document = PartyDocumentFactory(
            party=self.party,
            s3_key="thisisakey",
            name="doc1.pdf",
            safe=True,
        )

        url = reverse(
            "applications:party_document_stream",
            kwargs={
                "pk": str(another_application.pk),
                "party_pk": str(self.party.pk),
                "document_pk": str(party_document.pk),
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_party_document_stream_forbidden_organisation(self):
        other_organisation = self.create_organisation_with_exporter_user()[0]
        self.party.organisation = other_organisation
        self.party.save()
        self.application.organisation = other_organisation
        self.application.save()
        party_document = PartyDocumentFactory(
            party=self.party,
            s3_key="thisisakey",
            name="doc1.pdf",
            safe=True,
        )

        url = reverse(
            "applications:party_document_stream",
            kwargs={
                "pk": str(self.application.pk),
                "party_pk": str(self.party.pk),
                "document_pk": str(party_document.pk),
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
