import logging
from contextlib import closing

import requests
from django.conf import settings
from requests_toolbelt.multipart.encoder import MultipartEncoder

from conf.settings import REQUEST_TIMEOUT


class VirusScanException(Exception):
    """Exceptions raised when scanning documents for viruses."""


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
        requests-toolbelt expects this to return the number of unread bytes (instead of the total length of the stream)
        """

        return self._remaining_bytes


def scan_documents_file_for_viruses(document_id, filename, file):
    """Scans a file for viruses; returns True or False if a virus is detected."""

    if not file:
        raise VirusScanException(f"Document {document_id} has no file")

    with closing(file["Body"]):
        logging.info(f"Scanning document {document_id} for viruses")

        multipart_fields = {"file": (filename, S3StreamingBodyWrapper(file), file["ContentType"])}
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

        response.raise_for_status()
        report = response.json()

        if "malware" not in report:
            raise VirusScanException(f"Document {document_id} identified as malware: {response.text}")

        logging.info(f"Successfully scanned document {document_id}")

        return not report.get("malware")
