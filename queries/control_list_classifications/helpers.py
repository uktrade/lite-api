from django.http import Http404

from queries.control_list_classifications.models import ControlListClassificationQuery


def get_clc_query_by_pk(pk):
    try:
        return ControlListClassificationQuery.objects.get(pk=pk)
    except ControlListClassificationQuery.DoesNotExist:
        raise Http404
