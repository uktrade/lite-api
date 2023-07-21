from lite_content.lite_api import strings
from django.http import Http404

from api.core.exceptions import NotFoundError
from api.goods.models import Good, GoodDocument


def get_good(pk):
    try:
        return Good.objects.get(pk=pk)
    except Good.DoesNotExist:
        raise Http404


def get_good_document(good: Good, pk):
    """
    Returns a case or returns a 404 on failure
    """
    try:
        return GoodDocument.objects.get(good=good, pk=pk)
    except GoodDocument.DoesNotExist:
        raise NotFoundError({"document": strings.Documents.DOCUMENT_NOT_FOUND})


def get_good_with_organisation(pk, organisation_id):
    try:
        return Good.objects.get(pk=pk, organisation_id=organisation_id)
    except Good.DoesNotExist:
        raise Http404
