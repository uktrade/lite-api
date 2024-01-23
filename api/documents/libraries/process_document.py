import logging

from rest_framework import serializers

from api.documents.celery_tasks import scan_document_for_viruses, delete_document_from_s3

logger = logging.getLogger(__name__)


def process_document(document):
    try:
        document_id = str(document.id)
        scan_document_for_viruses.apply_async(args=(document_id,), link_error=delete_document_from_s3.si(document_id))
    except Exception:
        logger.exception("Error scanning document with id %s for viruses", document_id)
        raise serializers.ValidationError({"document": "Error scanning document for viruses"})
