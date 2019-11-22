from django.http import Http404

from applications.models import BaseApplication, GoodOnApplication
from conf.exceptions import NotFoundError
from content_strings.strings import get_string
from goods.models import Good, GoodDocument
from queries.control_list_classifications.models import ControlListClassificationQuery
from queries.helpers import get_exporter_query


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
        raise NotFoundError({"document": get_string("documents.document_not_found")})


def get_good_with_organisation(pk, organisation):
    try:
        good = Good.objects.get(pk=pk)

        if good.organisation.pk != organisation.pk:
            raise Http404

        return good
    except Good.DoesNotExist:
        raise Http404
