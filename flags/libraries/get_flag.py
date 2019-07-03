from django.http import Http404

from flags.models import Flag


def get_flag(pk):
    try:
        return Flag.objects.get(pk=pk)
    except Flag.DoesNotExist:
        raise Http404
