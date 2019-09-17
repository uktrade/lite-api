from conf.exceptions import NotFoundError
from queries.control_list_classifications.models import ControlListClassificationQuery
from queries.end_user_advisories.models import EndUserAdvisoryQuery


def get_exporter_query(pk):
    """
    Returns either a Control List Classification Query or
    a End User Classification Query depending on the PK given
    """
    try:
        return ControlListClassificationQuery.objects.get(pk=pk)
    except ControlListClassificationQuery.DoesNotExist:
        try:
            return EndUserAdvisoryQuery.objects.get(pk=pk)
        except EndUserAdvisoryQuery.DoesNotExist:
            raise NotFoundError({'query': 'Query not found - ' + str(pk)})
