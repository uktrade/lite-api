from ecju_queries.models import EcjuQuery
from conf.exceptions import NotFoundError


def get_ecju_queries_from_case(case):
    """
    Returns all the case notes from a case
    If is_visible_to_exporter is True, then only show case notes that are visible to exporters
    """
    return EcjuQuery.objects.filter(case=case).order_by('-created_at')
