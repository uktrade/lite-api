import logging
from background_task import background


from django.db.models import Q


# @shared_task()
@background(schedule=0, queue='document_av_scan_queue')
def prepare_document(document_id):
    from documents.models import Document
    doc = Document.objects.get(id=document_id)
    doc.prepare_document()


# @shared_task()
# def prepare_pending_documents():
#     from documents.models import Document
#     pending_docs = Document.objects.filter(
#         Q(checksum__isnull=True) |
#         Q(safe__isnull=True)
#     ).values_list('id', flat=True)
#     for doc_id in pending_docs:
#         prepare_document.delay(doc_id)
