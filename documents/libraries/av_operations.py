import logging
from contextlib import closing

import requests
from django.conf import settings
from requests_toolbelt.multipart.encoder import MultipartEncoder

from api.conf.settings import AV_REQUEST_TIMEOUT


class VirusScanException(Exception):
    """Exceptions raised when scanning documents for viruses."""


class S3StreamingBodyWrapper:
    """S3 Object wrapper that plays nice with streamed multipart/form-data."""

    def __init__(self, s3_obj):
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


def scan_file_for_viruses(document_id, filename, file):
    """Scans a file for viruses; returns True or False if a virus is detected."""

    with closing(file["Body"]):
        logging.info(f"AV scanning document '{document_id}' for viruses")

        multipart_fields = {"file": (filename, S3StreamingBodyWrapper(file), file["ContentType"])}
        encoder = MultipartEncoder(fields=multipart_fields)

        try:
            response = requests.post(
                # Assumes HTTP Basic auth in URL
                # see: https://github.com/uktrade/dit-clamav-rest
                settings.AV_SERVICE_URL.strip(),
                data=encoder,
                auth=(settings.AV_SERVICE_USERNAME.strip(), settings.AV_SERVICE_PASSWORD.strip()),
                headers={"Content-Type": encoder.content_type},
                timeout=AV_REQUEST_TIMEOUT,
            )
        except requests.exceptions.Timeout:
            raise VirusScanException(f"Timeout exceeded when AV scanning document '{document_id}'")
        except requests.exceptions.RequestException as exc:
            raise VirusScanException(
                f"An unexpected error occurred when AV scanning document '{document_id}' -> "
                f"{type(exc).__name__}: {exc}"
            )

        response.raise_for_status()
        report = response.json()

        # The response must contain the 'malware' key (its value will either be True or False)
        if "malware" not in report:
            raise VirusScanException(f"Failed to AV scan document {document_id}; 'malware' key not found in report")

        logging.info(f"Successfully AV scanned document '{document_id}'")

        contains_virus = report.get("malware")

        if contains_virus:
            logging.warning(f"Document '{document_id}' contains a virus; reason: {report.get('reason')}")

        return contains_virus
