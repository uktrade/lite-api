from django.http import Http404

from conf.exceptions import NotFoundError
from content_strings.strings import get_string

from goods.models import Good, GoodDocument


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
        raise NotFoundError({'document': get_string('documents.document_not_found')})
