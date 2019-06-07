from django.http import Http404

from goods.models import Good


def get_good(pk):
    try:
        return Good.objects.get(pk=pk)
    except Good.DoesNotExist:
        raise Http404
