from api.core.exceptions import NotFoundError
from api.queues.models import Queue


def get_queue(pk):
    """
    Returns the specified queue
    """
    try:
        return Queue.objects.get(pk=pk)
    except Queue.DoesNotExist:
        raise NotFoundError({"queue": "Queue not found - " + str(pk)})
