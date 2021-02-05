import datetime

from django.urls import reverse

from api.organisations.enums import OrganisationDocumentType
from test_helpers.clients import DataTestClient


class OrganisationDocumentViewTests(DataTestClient):
    def create_document_on_organisation(self, name):
        url = reverse("organisations:documents", kwargs={"pk": self.organisation.pk})
        data = {
            "document": {"name": name, "s3_key": name, "size": 476},
            "expiry_date": "2022-01-01",
            "reference_code": "123",
            "document_type": OrganisationDocumentType.FIREARM_SECTION_FIVE,
        }
        return self.client.post(url, data, **self.exporter_headers)

    def test_create_organisation_document(self):
        response = self.create_document_on_organisation("some-document")

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(self.organisation.document_on_organisations.count(), 1)

        instance = self.organisation.document_on_organisations.first()

        self.assertEqual(instance.document.name, "some-document")
        self.assertEqual(instance.document.s3_key, "some-document")
        self.assertEqual(instance.reference_code, "123")
        self.assertEqual(instance.document.size, 476)
        self.assertEqual(instance.expiry_date, datetime.date(2022, 1, 1))
        self.assertEqual(instance.document_type, OrganisationDocumentType.FIREARM_SECTION_FIVE)
        self.assertEqual(instance.organisation, self.organisation)

    def test_list_organisation_documents(self):
        self.assertEqual(self.create_document_on_organisation("some-document-one").status_code, 200)
        self.assertEqual(self.create_document_on_organisation("some-document-two").status_code, 200)
        self.assertEqual(self.create_document_on_organisation("some-document-three").status_code, 200)

        url = reverse("organisations:documents", kwargs={"pk": self.organisation.pk})

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["documents"]), 3)
