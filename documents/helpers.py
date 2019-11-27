import logging
import uuid

import boto3

from conf.settings import env
from lite_content.lite_api.documents import DocumentsEndpoint


class DocumentOperation:
    _client = None

    def get_client(self):
        if not self._client:
            self._client = boto3.client(
                "s3", aws_access_key_id=env("AWS_ACCESS_KEY_ID"), aws_secret_access_key=env("AWS_SECRET_ACCESS_KEY"),
            )
        return self._client

    @staticmethod
    def _get_bucket_name():
        return env("AWS_STORAGE_BUCKET_NAME")

    @staticmethod
    def generate_s3_key(document_name, file_extension):
        return f"{document_name}-{uuid.uuid4()}.{file_extension}"

    def upload_bytes_file(self, raw_file, s3_key):
        client = self.get_client()
        client.put_object(Bucket=self._get_bucket_name(), Key=s3_key, Body=raw_file)

    def delete_file(self, s3_key):
        client = self.get_client()
        try:
            client.delete_object(Bucket=self._get_bucket_name(), Key=s3_key)
        except Exception:  # noqa
            logging.warning(DocumentsEndpoint.DELETE_ERROR)
