from ecju_queries.models import EcjuQuery


def get_ecju_queries_from_case(case):
    """
    Returns all the ECJU queries from a case
    """
    return EcjuQuery.objects.filter(case=case).order_by('-created_at')
