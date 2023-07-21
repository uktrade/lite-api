from api.core.exceptions import NotFoundError
from api.queries.end_user_advisories.models import EndUserAdvisoryQuery


def get_exporter_query(pk):
    """
    Returns an End User Classification Query depending on the PK given
    """
    try:
        return EndUserAdvisoryQuery.objects.get(pk=pk)
    except EndUserAdvisoryQuery.DoesNotExist:
        raise NotFoundError({"query": "Query not found - " + str(pk)})
