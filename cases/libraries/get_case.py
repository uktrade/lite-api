from cases.models import Case
from conf.exceptions import NotFoundError


def get_case(pk):
    """
    Returns a case or returns a 404 on failure
    """
    try:
        return Case.objects.get(pk=pk)
    except Case.DoesNotExist:
        raise NotFoundError({'case': 'Case Note not found'})
