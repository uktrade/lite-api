from conf.settings import BACKGROUND_TASK_ENABLED
from rest_framework import serializers
from documents.tasks import prepare_document


def process_document(document):
    if BACKGROUND_TASK_ENABLED:
        prepare_document(str(document.id))
    else:
        try:
            prepare_document.now(str(document.id))
        except Exception:
            raise serializers.ValidationError({'errors': {'document': 'Failed to upload'}})
