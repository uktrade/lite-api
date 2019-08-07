from django.http import Http404

from ecju_queries.models import EcjuQuery


def get_ecju_query(pk):
    try:
        return EcjuQuery.objects.get(pk=pk)
    except EcjuQuery.DoesNotExist:
        raise Http404
