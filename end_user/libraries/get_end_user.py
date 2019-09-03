from django.http import Http404
from end_user.models import EndUser


def get_end_user(pk):
    try:
        return EndUser.objects.get(pk=pk)
    except EndUser.DoesNotExist:
        raise Http404
