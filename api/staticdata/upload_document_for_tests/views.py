import os

from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from api.core.authentication import SharedAuthentication
from api.conf.settings import env
from api.documents.libraries.s3_operations import init_s3_client


class UploadDocumentForTests(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        upload_document_endpoint_enabled = env("UPLOAD_DOCUMENT_ENDPOINT_ENABLED")

        if not upload_document_endpoint_enabled or upload_document_endpoint_enabled.lower() != "true":
            return JsonResponse(
                data={"errors": "This endpoint is not enabled"},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        s3 = init_s3_client()
        s3_key = "lite-e2e-test-file.txt"

        file_to_upload_abs_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "resources", "lite-e2e-test-file.txt")
        )

        try:
            s3.upload_file(file_to_upload_abs_path, settings.AWS_STORAGE_BUCKET_NAME, s3_key)
        except Exception as e:  # noqa
            if settings.DEBUG:
                raise
            return JsonResponse(
                data={"errors": "Error uploading file to S3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return JsonResponse(data={"s3_key": s3_key}, status=status.HTTP_200_OK)
