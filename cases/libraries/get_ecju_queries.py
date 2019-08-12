from cases.models import EcjuQuery
from conf.exceptions import NotFoundError


def get_ecju_queries_from_case(case):
    """
    Returns all the ECJU queries from a case
    """
    return EcjuQuery.objects.filter(case=case).order_by('-created_at')


def get_ecju_query(pk):
    try:
        return EcjuQuery.objects.get(pk=pk)
    except EcjuQuery.DoesNotExist:
        raise NotFoundError({'ecju_query': 'ECJU Query not found'})
