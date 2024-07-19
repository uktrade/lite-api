from django.urls import reverse
from rest_framework import status

from moto import mock_aws
from parameterized import parameterized

from django.http import FileResponse

from api.applications.models import GoodOnApplication
from test_helpers.clients import DataTestClient

from api.applications.tests.factories import StandardApplicationFactory
from api.goods.enums import GoodStatus
from api.goods.tests.factories import GoodFactory
from api.organisations.tests.factories import OrganisationFactory


# from nose.tools import assert_true
# import requests


class GoodDocumentsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.good = GoodFactory(organisation=self.organisation)
        self.url = reverse("goods:documents", kwargs={"pk": self.good.id})

    def test_can_view_all_documents_on_a_good(self):
        self.create_good_document(
            good=self.good, user=self.exporter_user, organisation=self.organisation, s3_key="doc1key", name="doc1.pdf"
        )
        self.create_good_document(
            good=self.good, user=self.exporter_user, organisation=self.organisation, s3_key="doc2key", name="doc2.pdf"
        )

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["documents"]), 2)

    def test_no_document_comments_saved(self):
        """
        Ensure no-doc comments by applicant are stored in the database
        """
        app = StandardApplicationFactory()
        org = OrganisationFactory()
        good = GoodFactory(organisation=OrganisationFactory())

        url = reverse("goods:good_document_availability", kwargs={"pk": good.id})
        payload = {"is_document_available": "no", "no_document_comments": "tezt"}
        response = self.client.post(url, payload, **self.exporter_headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        # Ensure fields updated
        good.refresh_from_db()
        assert good.is_document_available == False
        assert good.no_document_comments == "tezt"

    def test_submitted_good_cannot_have_docs_added(self):
        """
        Tests that the good cannot be edited after submission
        """
        draft = self.create_draft_standard_application(self.organisation)
        good_id = GoodOnApplication.objects.get(application=draft).good.id
        self.submit_application(draft)

        url = reverse("goods:documents", kwargs={"pk": good_id})
        data = {}
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submitted_good_cannot_have_docs_removed(self):
        """
        Tests that the good cannot be edited after submission
        """
        draft = self.create_draft_standard_application(self.organisation)
        good = GoodOnApplication.objects.get(application=draft).good
        document_1 = self.create_good_document(
            good=good, user=self.exporter_user, organisation=self.organisation, s3_key="doc1key", name="doc1.pdf"
        )
        self.submit_application(draft)

        url = reverse("goods:document", kwargs={"pk": good.id, "doc_pk": document_1.id})
        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_product_document_availability(self):
        draft = self.create_draft_standard_application(self.organisation)
        good = GoodOnApplication.objects.get(application=draft).good
        self.assertTrue(good.is_document_available)

        url = reverse("goods:good", kwargs={"pk": good.id})
        response = self.client.put(
            url,
            {"is_document_available": False, "no_document_comments": "Product not manufactured yet"},
            **self.exporter_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        good = response.json()["good"]
        self.assertFalse(good["is_document_available"])
        self.assertEqual(good["no_document_comments"], "Product not manufactured yet")

    def test_edit_product_document_sensitivity(self):
        draft = self.create_draft_standard_application(self.organisation)
        good = GoodOnApplication.objects.get(application=draft).good
        self.assertFalse(good.is_document_sensitive)

        url = reverse("goods:good", kwargs={"pk": good.id})
        response = self.client.put(url, {"is_document_sensitive": True}, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["good"]["is_document_sensitive"])

    def test_edit_product_document_description(self):
        draft = self.create_draft_standard_application(self.organisation)
        good = GoodOnApplication.objects.get(application=draft).good
        document = self.create_good_document(
            good=good, user=self.exporter_user, organisation=self.organisation, s3_key="doc1key", name="doc1.pdf"
        )
        url = reverse("goods:document", kwargs={"pk": good.id, "doc_pk": document.id})
        response = self.client.put(url, {"description": "Updated document description"}, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["document"]["description"], "Updated document description")


@mock_aws
class GoodDocumentStreamTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.good = GoodFactory(
            organisation=self.organisation,
            status=GoodStatus.DRAFT,
        )
        self.create_default_bucket()
        self.put_object_in_default_bucket("thisisakey", b"test")

    def test_get_good_document_stream(self):
        good_document = self.create_good_document(
            good=self.good,
            user=self.exporter_user,
            organisation=self.organisation,
            s3_key="thisisakey",
            name="doc1.pdf",
        )

        url = reverse(
            "goods:document_stream",
            kwargs={
                "pk": str(self.good.pk),
                "doc_pk": str(good_document.pk),
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response, FileResponse)
        self.assertEqual(b"".join(response.streaming_content), b"test")

    def test_get_good_document_stream_invalid_good_pk(self):
        another_good = GoodFactory(organisation=self.organisation)
        good_document = self.create_good_document(
            good=self.good,
            user=self.exporter_user,
            organisation=self.organisation,
            s3_key="thisisakey",
            name="doc1.pdf",
        )

        url = reverse(
            "goods:document_stream",
            kwargs={
                "pk": str(another_good.pk),
                "doc_pk": str(good_document.pk),
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_good_document_stream_other_organisation(self):
        other_organisation = self.create_organisation_with_exporter_user()[0]
        self.good.organisation = other_organisation
        self.good.save()
        good_document = self.create_good_document(
            good=self.good,
            user=self.exporter_user,
            organisation=other_organisation,
            s3_key="thisisakey",
            name="doc1.pdf",
        )

        url = reverse(
            "goods:document_stream",
            kwargs={
                "pk": str(self.good.pk),
                "doc_pk": str(good_document.pk),
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @parameterized.expand(
        [
            GoodStatus.SUBMITTED,
            GoodStatus.QUERY,
            GoodStatus.VERIFIED,
        ],
    )
    def test_get_good_document_stream_good_not_draft(self, good_status):
        self.good.status = good_status
        self.good.save()
        good_document = self.create_good_document(
            good=self.good,
            user=self.exporter_user,
            organisation=self.organisation,
            s3_key="thisisakey",
            name="doc1.pdf",
        )

        url = reverse(
            "goods:document_stream",
            kwargs={
                "pk": str(self.good.pk),
                "doc_pk": str(good_document.pk),
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
