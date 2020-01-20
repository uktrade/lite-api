from conf.exceptions import NotFoundError
from documents.libraries.s3_operations import download_document_from_s3
from documents.models import Document


def download_document(pk):
    try:
        document = Document.objects.get(id=pk)
        return download_document_from_s3(s3_key=document.s3_key, original_file_name=document.name)
    except Document.DoesNotExist:
        raise NotFoundError({"document": "Document not found"})
