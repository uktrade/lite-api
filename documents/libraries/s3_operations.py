import logging
import mimetypes
import uuid

import boto3
from django.http import StreamingHttpResponse
from s3chunkuploader.file_handler import S3FileUploadHandler

from conf.settings import env, STREAMING_CHUNK_SIZE

_client = boto3.client(
    "s3", aws_access_key_id=env("AWS_ACCESS_KEY_ID"), aws_secret_access_key=env("AWS_SECRET_ACCESS_KEY"),
)

_bucket_name = env("AWS_STORAGE_BUCKET_NAME")


# S3 operations
def get_object(key):
    return _client.get_object(Bucket=_bucket_name, Key=key)


def generate_s3_key(document_name, file_extension):
    return f"{document_name}-{uuid.uuid4()}.{file_extension}"


def upload_bytes_file(raw_file, s3_key):
    _client.put_object(Bucket=_bucket_name, Key=s3_key, Body=raw_file)


# Delete
def delete_file(s3_key):
    try:
        _client.delete_object(Bucket=_bucket_name, Key=s3_key)
    except Exception:  # noqa
        logging.warning("Failed to delete file")


# Download
def _generate_file(result):
    for chunk in iter(lambda: result["Body"].read(STREAMING_CHUNK_SIZE), b""):
        yield chunk


def document_download_stream(document):
    s3_response = get_object(document.s3_key)
    content_type = mimetypes.MimeTypes().guess_type(document.name)[0]
    response = StreamingHttpResponse(_generate_file(s3_response), content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.name}"'
    return response


def document_upload(request):
    if not request.FILES:
        return False, "No files attached"
    if len(request.FILES) != 1:
        return False, "Multiple files attached"

    file = request.FILES["file"]
