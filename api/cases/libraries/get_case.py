from api.cases.models import Case, CaseDocument
from api.core.exceptions import NotFoundError
from lite_content.lite_api import strings


def get_case(pk, include_draft=False, prefetch_related=None):
    """
    Returns a case or returns a 404 on failure.

    Lookups for related objects can be passed via prefetch_related
    as a list of strings.
    """
    try:
        if include_draft:
            qs = Case.objects.all()
        else:
            qs = Case.objects.submitted()

        if prefetch_related:
            for lookup in prefetch_related:
                qs = qs.prefetch_related(lookup)

        return qs.get(pk=pk)

    except Case.DoesNotExist:
        raise NotFoundError({"case": strings.Cases.CASE_NOT_FOUND})


def get_case_document(case: Case, s3_key: str):
    """
    Returns a case or returns a 404 on failure
    """
    try:
        return CaseDocument.objects.get(case=case, s3_key=s3_key)
    except CaseDocument.DoesNotExist:
        raise NotFoundError({"document": strings.Documents.DOCUMENT_NOT_FOUND})


def get_case_document_by_pk(pk):
    """
    Returns a case or returns a 404 on failure
    """
    try:
        return CaseDocument.objects.get(pk=pk)
    except CaseDocument.DoesNotExist:
        raise NotFoundError({"document": strings.Documents.DOCUMENT_NOT_FOUND})
