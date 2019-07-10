from django.http import Http404

from clc_queries.models import ClcQuery


def get_clc_query_by_pk(pk):
    try:
        return ClcQuery.objects.get(pk=pk)
    except ClcQuery.DoesNotExist:
        raise Http404
