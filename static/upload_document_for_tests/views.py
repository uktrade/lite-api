import os

import boto3
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from conf import constants
from conf.settings import env


class UploadDocumentForTests(APIView):
    def get(self, request):
        upload_document_endpoint_enabled = env("UPLOAD_DOCUMENT_ENDPOINT_ENABLED")

        if not upload_document_endpoint_enabled or upload_document_endpoint_enabled.lower() != "true":
            return JsonResponse(
                data={"errors": "This endpoint is not enabled"}, status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        # if "static.upload_document_for_tests" in str(request.__dict__):
        #     constants.skip_av_for_end_to_end_testing = 1

        # bucket_name = env("AWS_STORAGE_BUCKET_NAME")
        # s3 = boto3.client(
        #     "s3", aws_access_key_id=env("AWS_ACCESS_KEY_ID"), aws_secret_access_key=env("AWS_SECRET_ACCESS_KEY"),
        # )
        s3_key = "lite-e2e-test-file.txt"

        # file_to_upload_abs_path = os.path.abspath(
        #     os.path.join(os.path.dirname(__file__), "resources", "lite-e2e-test-file.txt")
        # )
        #
        # try:
        #     s3.upload_file(file_to_upload_abs_path, bucket_name, s3_key)
        # except Exception as e:  # noqa
        #     return JsonResponse(data={"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return JsonResponse(data={"s3_key": s3_key}, status=status.HTTP_200_OK)
