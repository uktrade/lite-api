from django.http import Http404
from queries.end_user_advisories.models import EndUserAdvisoryQuery


def get_end_user_advisory_by_pk(pk):
    try:
        return EndUserAdvisoryQuery.objects.get(pk=pk)
    except EndUserAdvisoryQuery.DoesNotExist:
        raise Http404
