import uuid

import boto3

from conf.settings import env


class DocumentOperation:
    @staticmethod
    def _get_bucket():
        return boto3.client(
            "s3", aws_access_key_id=env("AWS_ACCESS_KEY_ID"), aws_secret_access_key=env("AWS_SECRET_ACCESS_KEY"),
        )

    @staticmethod
    def _get_bucket_name():
        return env("AWS_STORAGE_BUCKET_NAME")

    def upload_bytes_file(self, raw_file, file_extension=None, s3_key=None):
        if not s3_key:
            s3_key = str(uuid.uuid4()) + file_extension
        bucket = self._get_bucket()
        bucket.put_object(Bucket=self._get_bucket_name(), Key=s3_key, Body=raw_file)
        return s3_key

    def delete_bytes_file(self, s3_key):
        bucket = self._get_bucket()
        bucket.delete_object(Bucket=self._get_bucket_name(), Key=s3_key)
