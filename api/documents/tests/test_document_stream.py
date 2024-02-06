import boto3

from moto import mock_aws

from django.http import StreamingHttpResponse
from django.urls import reverse

from test_helpers.clients import DataTestClient

from api.conf import settings
from api.documents.libraries.s3_operations import init_s3_client


@mock_aws
class DocumentStream(DataTestClient):
    def setUp(self):
        super().setUp()
        init_s3_client()
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_SECRET_ACCESS_KEY"],
            region_name=settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_REGION"],
        )
        s3.create_bucket(
            Bucket=settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_STORAGE_BUCKET_NAME"],
            CreateBucketConfiguration={
                "LocationConstraint": settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_REGION"],
            },
        )
        s3.put_object(
            Bucket=settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_STORAGE_BUCKET_NAME"],
            Key="thisisakey",
            Body=b"test",
        )

    def test_document_stream_as_caseworker(self):
        # given there is a case document
        case = self.create_standard_application_case(self.organisation)
        document = self.create_case_document(case=case, user=self.gov_user, name="jimmy")

        # when a caseworker tries to access it
        url = reverse("documents:document_stream", kwargs={"pk": document.pk})
        response = self.client.get(url, **self.gov_headers)

        # then they can
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, StreamingHttpResponse)
        self.assertEqual(b"".join(response.streaming_content), b"test")

    def test_document_stream_as_exporter(self):
        # given there is a case document that is visible to the exporter
        case = self.create_standard_application_case(self.organisation)
        document = self.create_case_document(case=case, user=self.gov_user, name="jimmy")

        # when the exporter tries to access it
        url = reverse("documents:document_stream", kwargs={"pk": document.pk})
        response = self.client.get(url, **self.exporter_headers)

        # then they can
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, StreamingHttpResponse)
        self.assertEqual(b"".join(response.streaming_content), b"test")

    def test_document_stream_as_exporter_on_invisible_document(self):
        # givem there is a document that's invisible to the exporter
        case = self.create_standard_application_case(self.organisation)
        document = self.create_case_document(case=case, user=self.gov_user, name="jimmy", visible_to_exporter=False)

        # when the exporter tries to access it
        url = reverse("documents:document_stream", kwargs={"pk": document.pk})
        response = self.client.get(url, **self.exporter_headers)

        # then they cannot
        self.assertEqual(response.status_code, 403)

    def test_document_stream_as_illegal_exporter(self):
        # given there is a case document in organisation a
        other_organisation, _ = self.create_organisation_with_exporter_user()
        case = self.create_standard_application_case(other_organisation)
        document = self.create_case_document(case=case, user=self.gov_user, name="jimmy", visible_to_exporter=False)

        url = reverse("documents:document_stream", kwargs={"pk": document.pk})

        # when user from organisation b tries to access it
        response = self.client.get(url, **self.exporter_headers)

        # then they are not able to
        self.assertEqual(response.status_code, 403)

    def test_document_stream_unsafe_file_as_caseworker(self):
        # given there is a case document
        case = self.create_standard_application_case(self.organisation)
        document = self.create_case_document(case=case, user=self.gov_user, name="jimmy", safe=False)

        # when a caseworker tries to access it
        url = reverse("documents:document_stream", kwargs={"pk": document.pk})
        response = self.client.get(url, **self.gov_headers)

        # then they can
        self.assertEqual(response.status_code, 404)

    def test_document_stream_unsafe_file_as_exporter(self):
        # given there is a case document that is visible to the exporter
        case = self.create_standard_application_case(self.organisation)
        document = self.create_case_document(case=case, user=self.gov_user, name="jimmy", safe=False)

        # when the exporter tries to access it
        url = reverse("documents:document_stream", kwargs={"pk": document.pk})
        response = self.client.get(url, **self.exporter_headers)

        # then they can
        self.assertEqual(response.status_code, 404)
