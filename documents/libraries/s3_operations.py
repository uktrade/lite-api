import logging
import uuid

import boto3

from conf.settings import env
from lite_content.lite_api.documents import DocumentsEndpoint

_client = boto3.client(
    "s3", aws_access_key_id=env("AWS_ACCESS_KEY_ID"), aws_secret_access_key=env("AWS_SECRET_ACCESS_KEY"),
)

_bucket_name = env("AWS_STORAGE_BUCKET_NAME")


def get_object(key):
    return _client.get_object(Bucket=_bucket_name, Key=key)


def generate_s3_key(document_name, file_extension):
    return f"{document_name}-{uuid.uuid4()}.{file_extension}"


def upload_bytes_file(raw_file, s3_key):
    _client.put_object(Bucket=_bucket_name, Key=s3_key, Body=raw_file)


def delete_file(s3_key):
    try:
        _client.delete_object(Bucket=_bucket_name, Key=s3_key)
    except Exception:  # noqa
        logging.warning(DocumentsEndpoint.DELETE_ERROR)
