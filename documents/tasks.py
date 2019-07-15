from background_task import background


@background(schedule=0, queue='document_av_scan_queue')
def prepare_document(document_id):
    from documents.models import Document
    doc = Document.objects.get(id=document_id)
    doc.prepare_document()
