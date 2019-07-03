from conf.exceptions import NotFoundError
from queues.models import Queue


def get_queue(pk):
    try:
        return Queue.objects.get(pk=pk)
    except Queue.DoesNotExist:
        raise NotFoundError({'queue': 'Queue not found'})
