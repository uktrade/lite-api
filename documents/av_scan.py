import logging
from contextlib import closing

import requests
from django.conf import settings
from django.utils.timezone import now
from django_pglocks import advisory_lock
from requests_toolbelt.multipart.encoder import MultipartEncoder

from conf.settings import REQUEST_TIMEOUT
from documents.libraries import s3_operations
from documents.models import Document


class S3StreamingBodyWrapper:
    """S3 Object wrapper that plays nice with streamed multipart/form-data."""

    def __init__(self, s3_obj):
        """Init wrapper, and grab interesting bits from s3 object."""
        self._obj = s3_obj
        self._body = s3_obj["Body"]
        self._remaining_bytes = s3_obj["ContentLength"]

    def read(self, amt=-1):
        """Read given amount of bytes, and decrease remaining len."""
        content = self._body.read(amt)
        self._remaining_bytes -= len(content)

        return content

    def __len__(self):
        """
        Return remaining bytes, that have not been read yet.
        requests-toolbelt expects this to return the number of unread bytes (rather than
        the total length of the stream).
        """
        return self._remaining_bytes


def virus_scan_document(document: Document):
    """
    Virus scans an uploaded document.
    This is intended to be run in the thread pool executor. The file is streamed from S3 to the
    anti-virus service.
    Any errors are logged and sent to Sentry.
    """
    logging.info(f"Scanning document {document.id} for viruses")
    with advisory_lock(f"av-scan-{document.id}"):
        _process_document(document)


def _process_document(document: Document):
    """Virus scans an uploaded document."""
    if not settings.AV_SERVICE_URL:
        raise VirusScanException(f"Cannot scan document {document.id}: AV service URL not configured")

    if document.virus_scanned_at is not None:
        logging.info(f"Skipping scan of document {document.id}: already performed on {document.virus_scanned_at}")
        return

    is_file_clean = _scan_s3_object(document.id, document.name, document.s3_key)

    if is_file_clean is not None:
        document.virus_scanned_at = now()
        document.safe = is_file_clean
        document.save()
        logging.info(f"Scan of document {document.id} successfully completed: safe={is_file_clean}")


def _scan_s3_object(document_id, original_filename, key):
    """Virus scans a file stored in S3."""
    response = s3_operations.get_object(key)  # Get the file from S3

    if not response:
        raise VirusScanException(f"Failed to retrieve document {document_id} from S3")

    with closing(response["Body"]):
        return _scan_raw_file(document_id, original_filename, S3StreamingBodyWrapper(response), response["ContentType"])


def _scan_raw_file(document_id, filename, file_object, content_type):
    """Virus scans a file-like object."""
    multipart_fields = {"file": (filename, file_object, content_type)}
    encoder = MultipartEncoder(fields=multipart_fields)

    try:
        response = requests.post(
            # Assumes HTTP Basic auth in URL
            # see: https://github.com/uktrade/dit-clamav-rest
            settings.AV_SERVICE_URL,
            data=encoder,
            auth=(settings.AV_SERVICE_USERNAME, settings.AV_SERVICE_PASSWORD),
            headers={"Content-Type": encoder.content_type},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        raise VirusScanException(f"Timeout exceeded when scanning document {document_id}")
    except requests.exceptions.RequestException as exc:
        raise VirusScanException(f"An unexpected error occurred when scanning document {document_id}: {exc}")

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise VirusScanException(
            f"Received an unexpected response when scanning document {document_id}: {response.status_code}"
        )

    try:
        report = response.json()
    except ValueError:
        raise VirusScanException(
            f"Received incorrect JSON from response when scanning document {document_id}: {response.text}"
        )

    if "malware" not in report:
        raise VirusScanException(f"Document {document_id} identified as malware: {response.text}")

    return not report.get("malware")


class VirusScanException(Exception):
    """Exceptions raised when scanning documents for viruses."""
