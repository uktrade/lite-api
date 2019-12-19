from lite_content.lite_api import strings
from django.http import Http404

from conf.exceptions import NotFoundError
from goods.models import Good, GoodDocument
from queries.control_list_classifications.models import ControlListClassificationQuery
from users.libraries.notifications import (
    get_exporter_user_notification_total_count,
    get_exporter_user_notification_individual_count,
)
from users.models import ExporterUser


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


def get_good_with_organisation(pk, organisation):
    try:
        good = Good.objects.get(pk=pk)

        if good.organisation.pk != organisation.pk:
            raise Http404

        return good
    except Good.DoesNotExist:
        raise Http404


def get_good_query_with_notifications(good: Good, exporter_user: ExporterUser, total_count: bool) -> dict:
    query = {}
    clc_query = ControlListClassificationQuery.objects.filter(good=good)

    if clc_query:
        clc_query = clc_query.first()
        query["id"] = clc_query.id

        exporter_user_notification_count = (
            get_exporter_user_notification_total_count(exporter_user=exporter_user, case=clc_query)
            if total_count
            else get_exporter_user_notification_individual_count(exporter_user=exporter_user, case=clc_query)
        )

        query["exporter_user_notification_count"] = exporter_user_notification_count

    return query
