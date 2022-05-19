import logging
import mimetypes
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ReadTimeoutError
from django.http import StreamingHttpResponse

from api.conf.settings import (
    STREAMING_CHUNK_SIZE,
    S3_CONNECT_TIMEOUT,
    AWS_S3_ENDPOINT_URL,
    S3_REQUEST_TIMEOUT,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    AWS_STORAGE_BUCKET_NAME,
)

_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
    config=Config(connect_timeout=S3_CONNECT_TIMEOUT, read_timeout=S3_REQUEST_TIMEOUT),
    **({"endpoint_url": AWS_S3_ENDPOINT_URL} if AWS_S3_ENDPOINT_URL else {}),
)


def get_object(document_id, s3_key):
    logging.info(f"Retrieving file '{s3_key}' on document '{document_id}'")

    try:
        return _client.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=s3_key)
    except ReadTimeoutError:
        logging.warning(f"Timeout exceeded when retrieving file '{s3_key}' on document '{document_id}'")
    except BotoCoreError as exc:
        logging.warning(
            f"An unexpected error occurred when retrieving file '{s3_key}' on document '{document_id}': {exc}"
        )


def generate_s3_key(document_name, file_extension):
    return f"{document_name}-{uuid.uuid4()}.{file_extension}"


def upload_bytes_file(raw_file, s3_key):
    _client.put_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=s3_key, Body=raw_file)


def delete_file(document_id, s3_key):
    logging.info(f"Deleting file '{s3_key}' on document '{document_id}'")

    try:
        _client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=s3_key)
    except ReadTimeoutError:
        logging.warning(f"Timeout exceeded when retrieving file '{s3_key}' on document '{document_id}'")
    except BotoCoreError as exc:
        logging.warning(
            f"An unexpected error occurred when deleting file '{s3_key}' on document '{document_id}': {exc}"
        )


def _stream_file(result):
    for chunk in iter(lambda: result["Body"].read(STREAMING_CHUNK_SIZE), b""):
        yield chunk


def document_download_stream(document):
    s3_response = get_object(document.id, document.s3_key)
    content_type = mimetypes.MimeTypes().guess_type(document.name)[0]

    response = StreamingHttpResponse(streaming_content=_stream_file(s3_response), content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.name}"'

    return response
