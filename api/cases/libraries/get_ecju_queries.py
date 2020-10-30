from api.cases import models
from api.core.exceptions import NotFoundError
from lite_content.lite_api import strings


def get_ecju_queries_from_case(case):
    """
    Returns all the ECJU queries from a case
    """
    return models.EcjuQuery.objects.filter(case=case).order_by("-created_at")


def get_ecju_query(pk):
    try:
        return models.EcjuQuery.objects.get(pk=pk)
    except models.EcjuQuery.DoesNotExist:
        raise NotFoundError({"ecju_query": "ECJU Query not found - " + str(pk)})


def get_ecju_query_document(query, pk):
    try:
        return models.EcjuQueryDocument.objects.get(query=query, pk=pk)
    except models.EcjuQueryDocument.DoesNotExist:
        raise NotFoundError({"document": strings.EcjuQuery.DOCUMENT_NOT_FOUND})
