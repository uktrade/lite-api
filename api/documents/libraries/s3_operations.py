import logging
import mimetypes
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ReadTimeoutError

from django.conf import settings
from django.http import FileResponse


_client = None


def init_s3_client():
    # We want to instantiate this once, ideally, but there may be cases where we
    # want to explicitly re-instiate the client e.g. in tests.
    global _client
    additional_s3_params = {}
    if settings.AWS_ENDPOINT_URL:
        additional_s3_params["endpoint_url"] = settings.AWS_ENDPOINT_URL
    _client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        config=Config(connect_timeout=settings.S3_CONNECT_TIMEOUT, read_timeout=settings.S3_REQUEST_TIMEOUT),
        **additional_s3_params,
    )
    return _client


init_s3_client()


def get_object(document_id, s3_key):
    logging.info(f"Retrieving file '{s3_key}' on document '{document_id}'")

    try:
        return _client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
    except ReadTimeoutError:
        logging.warning(f"Timeout exceeded when retrieving file '{s3_key}' on document '{document_id}'")
    except BotoCoreError as exc:
        logging.warning(
            f"An unexpected error occurred when retrieving file '{s3_key}' on document '{document_id}': {exc}"
        )


def generate_s3_key(document_name, file_extension):
    return f"{document_name}-{uuid.uuid4()}.{file_extension}"


def upload_bytes_file(raw_file, s3_key):
    _client.put_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key, Body=raw_file)


def delete_file(document_id, s3_key):
    logging.info(f"Deleting file '{s3_key}' on document '{document_id}'")

    try:
        _client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
    except ReadTimeoutError:
        logging.warning(f"Timeout exceeded when retrieving file '{s3_key}' on document '{document_id}'")
    except BotoCoreError as exc:
        logging.warning(
            f"An unexpected error occurred when deleting file '{s3_key}' on document '{document_id}': {exc}"
        )


def document_download_stream(document):
    s3_response = get_object(document.id, document.s3_key)
    content_type = mimetypes.MimeTypes().guess_type(document.name)[0]

    response = FileResponse(
        s3_response["Body"],
        as_attachment=True,
        filename=document.name,
    )
    response["Content-Type"] = content_type

    return response
