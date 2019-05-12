from django.http import Http404

from cases.models import Case


def get_case(pk):
    try:
        return Case.objects.get(pk=pk)
    except Case.DoesNotExist:
        raise Http404
