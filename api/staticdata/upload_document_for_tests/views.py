import os

import boto3
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from api.core.authentication import SharedAuthentication
from api.conf.settings import env, AWS_STORAGE_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY


class UploadDocumentForTests(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        upload_document_endpoint_enabled = env("UPLOAD_DOCUMENT_ENDPOINT_ENABLED")

        if not upload_document_endpoint_enabled or upload_document_endpoint_enabled.lower() != "true":
            return JsonResponse(
                data={"errors": "This endpoint is not enabled"}, status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY,)
        s3_key = "lite-e2e-test-file.txt"

        file_to_upload_abs_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "resources", "lite-e2e-test-file.txt")
        )

        try:
            s3.upload_file(file_to_upload_abs_path, AWS_STORAGE_BUCKET_NAME, s3_key)
        except Exception as e:  # noqa
            return JsonResponse(data={"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return JsonResponse(data={"s3_key": s3_key}, status=status.HTTP_200_OK)
