import datetime

from unittest import mock

from moto import mock_aws

from django.http import FileResponse
from django.urls import reverse

from api.organisations.enums import OrganisationDocumentType
from api.organisations.models import DocumentOnOrganisation
from api.organisations.tests.factories import DocumentOnOrganisationFactory
from test_helpers.clients import DataTestClient


class OrganisationDocumentViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.document_data = {
            "name": "updated_document_name.pdf",
            "s3_key": "s3_keykey.pdf",
            "size": 123456,
        }

    @mock.patch("api.documents.libraries.s3_operations.get_object")
    @mock.patch("api.documents.libraries.av_operations.scan_file_for_viruses")
    def test_create_organisation_document(self, mock_virus_scan, mock_s3_operations_get_object):
        mock_s3_operations_get_object.return_value = self.document_data
        mock_virus_scan.return_value = False

        url = reverse("organisations:documents", kwargs={"pk": self.organisation.pk})
        data = {
            "document": {"name": "some-document", "s3_key": "some-document", "size": 476},
            "expiry_date": "2026-01-01",
            "reference_code": "123",
            "document_type": OrganisationDocumentType.FIREARM_SECTION_FIVE,
        }
        response = self.client.post(url, data, **self.exporter_headers)

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

    @mock.patch("api.documents.libraries.s3_operations.get_object")
    @mock.patch("api.documents.libraries.av_operations.scan_file_for_viruses")
    def test_create_organisation_document_other_organisation(self, mock_virus_scan, mock_s3_operations_get_object):
        mock_s3_operations_get_object.return_value = self.document_data
        mock_virus_scan.return_value = False
        other_organisation, _ = self.create_organisation_with_exporter_user()
        url = reverse("organisations:documents", kwargs={"pk": other_organisation.pk})

        data = {
            "document": {"name": "some-document", "s3_key": "some-document", "size": 476},
            "expiry_date": "2026-01-01",
            "reference_code": "123",
            "document_type": OrganisationDocumentType.FIREARM_SECTION_FIVE,
        }
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, 403)

    def test_list_organisation_documents(self):
        DocumentOnOrganisationFactory.create(
            document__name="some-document-one",
            document__s3_key="thisisakey",
            document__safe=True,
            organisation=self.organisation,
        )
        DocumentOnOrganisationFactory.create(
            document__name="some-document-two",
            document__s3_key="thisisakey",
            document__safe=True,
            organisation=self.organisation,
        )
        DocumentOnOrganisationFactory.create(
            document__name="some-document-three",
            document__s3_key="thisisakey",
            document__safe=True,
            organisation=self.organisation,
        )
        other_organisation, _ = self.create_organisation_with_exporter_user()
        DocumentOnOrganisationFactory.create(
            document__name="other-organisation-some-document-three",
            document__s3_key="thisisakey",
            document__safe=True,
            organisation=other_organisation,
        )

        url = reverse("organisations:documents", kwargs={"pk": self.organisation.pk})

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["documents"]), 3)

    def test_list_organisation_documents_other_organisation(self):
        other_organisation, _ = self.create_organisation_with_exporter_user()
        url = reverse("organisations:documents", kwargs={"pk": other_organisation.pk})

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, 403)

    def test_retrieve_organisation_documents(self):
        document_on_application = DocumentOnOrganisationFactory.create(
            organisation=self.organisation,
            expiry_date=datetime.date(2026, 1, 1),
            document_type=OrganisationDocumentType.FIREARM_SECTION_FIVE,
            reference_code="123",
            document__name="some-document-one",
            document__s3_key="some-document-one",
            document__size=476,
            document__safe=True,
        )

        url = reverse(
            "organisations:documents",
            kwargs={"pk": self.organisation.pk, "document_on_application_pk": document_on_application.pk},
        )

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "id": str(document_on_application.pk),
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
                    "safe": True,
                    "id": mock.ANY,
                },
            },
        )

    def test_retrieve_organisation_documents_invalid_organisation(self):
        other_organisation, _ = self.create_organisation_with_exporter_user()
        document_on_application = DocumentOnOrganisationFactory.create(
            organisation=other_organisation,
            expiry_date=datetime.date(2026, 1, 1),
            document_type=OrganisationDocumentType.FIREARM_SECTION_FIVE,
            reference_code="123",
            document__name="some-document-one",
            document__s3_key="some-document-one",
            document__size=476,
            document__safe=True,
        )

        url = reverse(
            "organisations:documents",
            kwargs={"pk": other_organisation.pk, "document_on_application_pk": document_on_application.pk},
        )

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, 403)

    def test_delete_organisation_documents(self):
        document_on_application = DocumentOnOrganisationFactory.create(organisation=self.organisation)

        url = reverse(
            "organisations:documents",
            kwargs={
                "pk": self.organisation.pk,
                "document_on_application_pk": document_on_application.pk,
            },
        )

        response = self.client.delete(url, **self.exporter_headers)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(DocumentOnOrganisation.DoesNotExist):
            DocumentOnOrganisation.objects.get(pk=document_on_application.pk)

    def test_delete_organisation_document_other_organisation(self):
        other_organisation, _ = self.create_organisation_with_exporter_user()
        document_on_application = DocumentOnOrganisationFactory.create(organisation=other_organisation)

        url = reverse(
            "organisations:documents",
            kwargs={
                "pk": other_organisation.pk,
                "document_on_application_pk": document_on_application.pk,
            },
        )

        response = self.client.delete(url, **self.exporter_headers)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(DocumentOnOrganisation.objects.filter(pk=document_on_application.pk).exists())

    def test_update_organisation_documents(self):
        document_on_application = DocumentOnOrganisationFactory.create(organisation=self.organisation)

        url = reverse(
            "organisations:documents",
            kwargs={
                "pk": self.organisation.pk,
                "document_on_application_pk": document_on_application.pk,
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

        document_on_application.refresh_from_db()
        self.assertEqual(
            document_on_application.expiry_date,
            datetime.date(2030, 12, 12),
        )
        self.assertEqual(
            document_on_application.reference_code,
            "567",
        )

    def test_update_organisation_documents_other_organisation(self):
        other_organisation, _ = self.create_organisation_with_exporter_user()
        document_on_application = DocumentOnOrganisationFactory.create(organisation=other_organisation)

        url = reverse(
            "organisations:documents",
            kwargs={
                "pk": other_organisation.pk,
                "document_on_application_pk": document_on_application.pk,
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
        self.assertEqual(response.status_code, 403)


@mock_aws
class DocumentOnOrganisationStreamViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.create_default_bucket()
        self.put_object_in_default_bucket("thisisakey", b"test")

    def test_document_stream_as_caseworker(self):
        document_on_application = DocumentOnOrganisationFactory.create(
            document__s3_key="thisisakey",
            document__safe=True,
            organisation=self.organisation,
        )

        url = reverse(
            "organisations:document_stream",
            kwargs={
                "pk": self.organisation.pk,
                "document_on_application_pk": document_on_application.pk,
            },
        )
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, FileResponse)
        self.assertEqual(b"".join(response.streaming_content), b"test")

    def test_document_stream_as_exporter(self):
        document_on_application = DocumentOnOrganisationFactory.create(
            document__s3_key="thisisakey",
            document__safe=True,
            organisation=self.organisation,
        )

        url = reverse(
            "organisations:document_stream",
            kwargs={
                "pk": self.organisation.pk,
                "document_on_application_pk": document_on_application.pk,
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, FileResponse)
        self.assertEqual(b"".join(response.streaming_content), b"test")

    def test_unsafe_document_stream_as_caseworker(self):
        document_on_application = DocumentOnOrganisationFactory.create(
            document__s3_key="thisisakey",
            document__safe=False,
            organisation=self.organisation,
        )

        url = reverse(
            "organisations:document_stream",
            kwargs={
                "pk": self.organisation.pk,
                "document_on_application_pk": document_on_application.pk,
            },
        )
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 404)

    def test_unsafe_document_stream_as_exporter(self):
        document_on_application = DocumentOnOrganisationFactory.create(
            document__s3_key="thisisakey",
            document__safe=False,
            organisation=self.organisation,
        )

        url = reverse(
            "organisations:document_stream",
            kwargs={
                "pk": self.organisation.pk,
                "document_on_application_pk": document_on_application.pk,
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, 404)

    def test_document_stream_as_exporter_on_other_organisation(self):
        other_organisation, _ = self.create_organisation_with_exporter_user()
        document_on_application = DocumentOnOrganisationFactory.create(
            document__s3_key="thisisakey",
            document__safe=True,
            organisation=other_organisation,
        )

        url = reverse(
            "organisations:document_stream",
            kwargs={
                "pk": other_organisation.pk,
                "document_on_application_pk": document_on_application.pk,
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, 403)
