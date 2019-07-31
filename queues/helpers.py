from conf.exceptions import NotFoundError
from conf.settings import ALL_CASES_SYSTEM_QUEUE_ID, OPEN_CASES_SYSTEM_QUEUE_ID
from queues.models import Queue
from teams.models import Team


def get_all_cases_queue():
    return Queue(id=ALL_CASES_SYSTEM_QUEUE_ID,
                 name='All cases',
                 team=Team.objects.get(name='Admin'))


def get_open_cases_queue():
    return Queue(id=OPEN_CASES_SYSTEM_QUEUE_ID,
                 name='Open cases',
                 team=Team.objects.get(name='Admin'))


def get_queue(pk):
    if ALL_CASES_SYSTEM_QUEUE_ID == str(pk):
        return get_all_cases_queue()
    try:
        return Queue.objects.get(pk=pk)
    except Queue.DoesNotExist:
        raise NotFoundError({'queue': 'Queue not found'})
