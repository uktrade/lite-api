import logging
import mimetypes
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ReadTimeoutError
from django.http import StreamingHttpResponse

from conf.settings import env, STREAMING_CHUNK_SIZE, DB_CONNECT_TIMEOUT, EXTERNAL_REQUEST_TIMEOUT

_client = boto3.client(
    "s3",
    aws_access_key_id=env("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=env("AWS_SECRET_ACCESS_KEY"),
    region_name=env("AWS_REGION"),
    config=Config(connect_timeout=DB_CONNECT_TIMEOUT, read_timeout=EXTERNAL_REQUEST_TIMEOUT),
)

_bucket_name = env("AWS_STORAGE_BUCKET_NAME")


def get_object(document_id, s3_key):
    logging.info(f"Retrieving file '{s3_key}' on document '{document_id}'")

    try:
        return _client.get_object(Bucket=_bucket_name, Key=s3_key)
    except ReadTimeoutError:
        logging.warning(f"Timeout exceeded when retrieving file '{s3_key}' on document '{document_id}'")
    except BotoCoreError as exc:
        logging.warning(
            f"An unexpected error occurred when retrieving file '{s3_key}' on document '{document_id}': {exc}"
        )


def generate_s3_key(document_name, file_extension):
    return f"{document_name}-{uuid.uuid4()}.{file_extension}"


def upload_bytes_file(raw_file, s3_key):
    _client.put_object(Bucket=_bucket_name, Key=s3_key, Body=raw_file)


def delete_file(document_id, s3_key):
    logging.info(f"Deleting file '{s3_key}' on document '{document_id}'")

    try:
        _client.delete_object(Bucket=_bucket_name, Key=s3_key)
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
    response = StreamingHttpResponse(_stream_file(s3_response), content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.name}"'
    return response
