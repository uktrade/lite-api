import datetime
from unittest import mock

from django.urls import reverse

from api.organisations.enums import OrganisationDocumentType
from api.organisations.models import DocumentOnOrganisation
from test_helpers.clients import DataTestClient


class OrganisationDocumentViewTests(DataTestClient):
    def create_document_on_organisation(self, name):
        url = reverse("organisations:documents", kwargs={"pk": self.organisation.pk})
        data = {
            "document": {"name": name, "s3_key": name, "size": 476},
            "expiry_date": "2026-01-01",
            "reference_code": "123",
            "document_type": OrganisationDocumentType.FIREARM_SECTION_FIVE,
        }
        return self.client.post(url, data, **self.exporter_headers)

    @mock.patch("api.documents.tasks.scan_document_for_viruses.now", mock.Mock)
    def test_create_organisation_document(self):
        response = self.create_document_on_organisation("some-document")

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(self.organisation.document_on_organisations.count(), 1)

        instance = self.organisation.document_on_organisations.first()

        self.assertEqual(instance.document.name, "some-document")
        self.assertEqual(instance.document.s3_key, "some-document")
        self.assertEqual(instance.reference_code, "123")
        self.assertEqual(instance.document.size, 476)
        self.assertEqual(instance.expiry_date, datetime.date(2026, 1, 1))
        self.assertEqual(instance.document_type, OrganisationDocumentType.FIREARM_SECTION_FIVE)
        self.assertEqual(instance.organisation, self.organisation)

    @mock.patch("api.documents.tasks.scan_document_for_viruses.now", mock.Mock)
    def test_list_organisation_documents(self):
        self.assertEqual(self.create_document_on_organisation("some-document-one").status_code, 201)
        self.assertEqual(self.create_document_on_organisation("some-document-two").status_code, 201)
        self.assertEqual(self.create_document_on_organisation("some-document-three").status_code, 201)

        url = reverse("organisations:documents", kwargs={"pk": self.organisation.pk})

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["documents"]), 3)

    @mock.patch("api.documents.tasks.scan_document_for_viruses.now", mock.Mock)
    def test_retrieve_organisation_documents(self):
        response = self.create_document_on_organisation("some-document-one")
        self.assertEqual(response.status_code, 201)

        document_on_application_pk = response.json()["document"]["id"]

        url = reverse(
            "organisations:documents",
            kwargs={"pk": self.organisation.pk, "document_on_application_pk": document_on_application_pk},
        )

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": document_on_application_pk,
                "expiry_date": "01 January 2026",
                "document_type": "section-five-certificate",
                "organisation": str(self.organisation.id),
                "is_expired": False,
                "reference_code": "123",
                "document": {
                    "name": "some-document-one",
                    "s3_key": "some-document-one",
                    "size": 476,
                    "created_at": mock.ANY,
                    "safe": None,
                    "id": mock.ANY,
                },
            },
        )

    @mock.patch("api.documents.tasks.scan_document_for_viruses.now", mock.Mock)
    def test_delete_organisation_documents(self):
        response = self.create_document_on_organisation("some-document-one")
        self.assertEqual(response.status_code, 201)

        document_on_application_pk = response.json()["document"]["id"]

        url = reverse(
            "organisations:documents",
            kwargs={
                "pk": self.organisation.pk,
                "document_on_application_pk": document_on_application_pk,
            },
        )

        response = self.client.delete(url, **self.exporter_headers)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(DocumentOnOrganisation.DoesNotExist):
            DocumentOnOrganisation.objects.get(pk=document_on_application_pk)

    @mock.patch("api.documents.tasks.scan_document_for_viruses.now", mock.Mock)
    def test_update_organisation_documents(self):
        response = self.create_document_on_organisation("some-document-one")
        self.assertEqual(response.status_code, 201)

        document_on_application_pk = response.json()["document"]["id"]

        url = reverse(
            "organisations:documents",
            kwargs={
                "pk": self.organisation.pk,
                "document_on_application_pk": document_on_application_pk,
            },
        )

        response = self.client.put(
            url,
            data={
                "expiry_date": "2030-12-12",
                "reference_code": "567",
            },
            **self.exporter_headers,
        )
        self.assertEqual(response.status_code, 200)

        document_on_application = DocumentOnOrganisation.objects.get(pk=document_on_application_pk)
        self.assertEqual(
            document_on_application.expiry_date,
            datetime.date(2030, 12, 12),
        )
        self.assertEqual(
            document_on_application.reference_code,
            "567",
        )
