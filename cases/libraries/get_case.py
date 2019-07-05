from cases.models import Case, CaseDocument
from conf.exceptions import NotFoundError


def get_case(pk):
    """
    Returns a case or returns a 404 on failure
    """
    try:
        return Case.objects.get(pk=pk)
    except Case.DoesNotExist:
        raise NotFoundError({'case': 'Queue not found'})


def get_case_document(case: Case, s3_key: str):
    """
    Returns a case or returns a 404 on failure
    """
    try:
        return CaseDocument.objects.get(case=case, s3_key=s3_key)
    except CaseDocument.DoesNotExist:
        raise NotFoundError({'document': 'Queue not found'})


def get_case_document_by_pk(pk):
    """
    Returns a case or returns a 404 on failure
    """
    try:
        return CaseDocument.objects.get(pk=pk)
    except CaseDocument.DoesNotExist:
        raise NotFoundError({'document': 'Queue not found'})
