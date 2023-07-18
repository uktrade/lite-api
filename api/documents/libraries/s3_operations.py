import boto3
import logging
import uuid

from botocore.config import Config
from botocore.exceptions import BotoCoreError, ReadTimeoutError

from django.conf import settings


def get_client():
    additional_s3_params = {}
    if settings.AWS_ENDPOINT_URL:
        additional_s3_params["endpoint_url"] = settings.AWS_ENDPOINT_URL

    config = Config(connect_timeout=settings.S3_CONNECT_TIMEOUT, read_timeout=settings.S3_REQUEST_TIMEOUT)

    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        config=config,
        **additional_s3_params,
    )


_client = get_client()


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
