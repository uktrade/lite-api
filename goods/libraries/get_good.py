from django.http import Http404

from applications.models import Application, GoodOnApplication
from conf.exceptions import NotFoundError
from content_strings.strings import get_string

from goods.models import Good, GoodDocument
from queries.control_list_classifications.models import ControlListClassificationQuery


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


def get_goods_from_case(case):
    if case.clc_query:
        return [ControlListClassificationQuery.objects.get(case=case).good.id]
    else:
        application = Application.objects.get(case=case)
        goods_on_applications = GoodOnApplication.objects.filter(application=application)
        return [x.good.id for x in goods_on_applications]
