from conf.exceptions import NotFoundError
from queries.control_list_classifications.models import ControlListClassificationQuery


def get_clc_query_by_good(good):
    try:
        return ControlListClassificationQuery.objects.get(good=good)
    except ControlListClassificationQuery.DoesNotExist:
        raise NotFoundError({'control_list_classification': 'Control List Classification not found'})
