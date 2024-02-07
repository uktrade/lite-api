import logging
import mimetypes
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ReadTimeoutError, ClientError

from django.conf import settings
from django.http import FileResponse

logger = logging.getLogger(__name__)

_processed_client = None
_staged_client = None


def init_s3_client():
    # We want to instantiate this once, ideally, but there may be cases where we
    # want to explicitly re-instiate the client e.g. in tests.
    global _processed_client
    global _staged_client
    additional_s3_params = {}
    if settings.AWS_ENDPOINT_URL:
        additional_s3_params["endpoint_url"] = settings.AWS_ENDPOINT_URL

    _processed_client = boto3.client(
        "s3",
        aws_access_key_id=settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_SECRET_ACCESS_KEY"],
        region_name=settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_REGION"],
        config=Config(connect_timeout=settings.S3_CONNECT_TIMEOUT, read_timeout=settings.S3_REQUEST_TIMEOUT),
        **additional_s3_params,
    )
    _staged_client = boto3.client(
        "s3",
        aws_access_key_id=settings.FILE_UPLOAD_STAGED_BUCKET["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=settings.FILE_UPLOAD_STAGED_BUCKET["AWS_SECRET_ACCESS_KEY"],
        region_name=settings.FILE_UPLOAD_STAGED_BUCKET["AWS_REGION"],
        config=Config(connect_timeout=settings.S3_CONNECT_TIMEOUT, read_timeout=settings.S3_REQUEST_TIMEOUT),
        **additional_s3_params,
    )
    return {"staged": _staged_client, "processed": _processed_client}


init_s3_client()


def _get_bucket_client(bucket):
    if bucket == "processed":
        return _processed_client, settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_STORAGE_BUCKET_NAME"]
    elif bucket == "staged":
        return _staged_client, settings.FILE_UPLOAD_STAGED_BUCKET["AWS_STORAGE_BUCKET_NAME"]
    else:
        raise Exception(f"No S3 bucket exists with label '{bucket}'")


def get_object(document_id, s3_key, bucket="processed"):
    logger.info(f"Retrieving file '{s3_key}' on document '{document_id}' from bucket '{bucket}'")
    aws_client, bucket_name = _get_bucket_client(bucket)

    try:
        return aws_client.get_object(Bucket=bucket_name, Key=s3_key)
    except ReadTimeoutError:
        logger.warning(f"Timeout exceeded when retrieving file '{s3_key}' on document '{document_id}'")
    except BotoCoreError as exc:
        logger.warning(
            f"An unexpected error occurred when retrieving file '{s3_key}' on document '{document_id}': {exc}"
        )


def move_staged_document_to_processed(document_id, s3_key):
    logger.info(f"Moving file '{s3_key}' on document '{document_id}' from staged bucket to processed bucket")
    # Grab the document from the staged S3 bucket
    try:
        staged_document = get_object(document_id, s3_key, "staged")

    except ClientError as exc:
        logger.warning(f"An error occurred when retrieving file '{s3_key}' on document '{document_id}': {exc}")
        # TODO: When we move over to using two S3 buckets, we should make this raise an exception.
        #   For now, this keeps us backward compatible so that we can switch from
        #   a single S3 bucket to staged/processed buckets more smoothly
        return

    # Upload the document to the processed S3 bucket
    # NOTE: Ideally we would use AWS' copy operation to copy from bucket to bucket.
    #  However, the IAM credentials we are using are limited with individual credentials having
    #  read/write for ONE bucket only - for copying, we would need credentials with read for the
    #  staged bucket and write for the processed bucket. This might be something to investigate
    #  with SRE later.
    processed_aws_client, processed_bucket_name = _get_bucket_client("processed")
    processed_aws_client.put_object(Bucket=processed_bucket_name, Key=s3_key, Body=staged_document["Body"].read())

    # Delete the document from the staged S3 bucket now we have moved it successfully
    delete_file(document_id, s3_key, bucket="staged")


def generate_s3_key(document_name, file_extension):
    return f"{document_name}-{uuid.uuid4()}.{file_extension}"


def upload_bytes_file(raw_file, s3_key, bucket="processed"):
    aws_client, bucket_name = _get_bucket_client(bucket)
    aws_client.put_object(Bucket=bucket_name, Key=s3_key, Body=raw_file)


def delete_file(document_id, s3_key, bucket="processed"):
    logger.info(f"Deleting file '{s3_key}' on document '{document_id}' from bucket '{bucket}'")
    aws_client, bucket_name = _get_bucket_client(bucket)

    try:
        aws_client.delete_object(Bucket=bucket_name, Key=s3_key)
    except ReadTimeoutError:
        logger.warning(f"Timeout exceeded when retrieving file '{s3_key}' on document '{document_id}'")
    except BotoCoreError as exc:
        logger.warning(f"An unexpected error occurred when deleting file '{s3_key}' on document '{document_id}': {exc}")


def document_download_stream(document):
    s3_response = get_object(document.id, document.s3_key, "processed")
    content_type = mimetypes.MimeTypes().guess_type(document.name)[0]

    response = FileResponse(
        s3_response["Body"],
        as_attachment=True,
        filename=document.name,
    )
    response["Content-Type"] = content_type

    return response
