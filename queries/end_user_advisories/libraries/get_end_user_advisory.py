from conf.exceptions import NotFoundError
from queries.end_user_advisories.models import EndUserAdvisoryQuery


def get_end_user_advisory_by_pk(pk):
    try:
        return EndUserAdvisoryQuery.objects.get(pk=pk)
    except EndUserAdvisoryQuery.DoesNotExist:
        raise NotFoundError({"end_user_advisory": "end user advisory not found"})
