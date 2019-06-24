from django.http import Http404

from queues.models import Queue


def get_queue(pk):
    try:
        return Queue.objects.get(pk=pk)
    except Queue.DoesNotExist:
        raise Http404
