import logging

from rest_framework import serializers

from api.documents.celery_tasks import process_uploaded_document, delete_document_from_s3

logger = logging.getLogger(__name__)


def process_document(document):
    try:
        document_id = str(document.id)
        process_uploaded_document.apply_async(args=(document_id,), link_error=delete_document_from_s3.si(document_id))
    except Exception:
        logger.exception("Error processing document with id %s", document_id)
        raise serializers.ValidationError({"document": "Error processing document"})
