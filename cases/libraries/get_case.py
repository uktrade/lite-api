from django.http import Http404

from cases.models import Case


def get_case(pk):
    """
    Returns a case or returns a 404 on failure
    """
    try:
        return Case.objects.get(pk=pk)
    except Case.DoesNotExist:
        raise Http404
