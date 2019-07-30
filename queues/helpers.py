from conf.exceptions import NotFoundError
from conf.settings import ALL_CASES_SYSTEM_QUEUE_ID, ADMIN_TEAM_ID
from queues.models import Queue
from teams.models import Team


#TODO rename to create instead of get
def get_all_cases_queue():
    all_cases_queue = Queue(id=ALL_CASES_SYSTEM_QUEUE_ID,
                            name='All cases',
                            team=Team.objects.get(name='Admin')
                            )
    return all_cases_queue


def get_queue(pk):
    if ALL_CASES_SYSTEM_QUEUE_ID == str(pk):
        return get_all_cases_queue()
    try:
        return Queue.objects.get(pk=pk)
    except Queue.DoesNotExist:
        raise NotFoundError({'queue': 'Queue not found'})


#TODO this was constructing the object the old fashioned way, probably not needed
def get_all_cases_queue_old():
    all_cases_queue = {
        'queue': {
            'id': ALL_CASES_SYSTEM_QUEUE_ID,
            'name': 'All cases',
            'team': {
                'id': ADMIN_TEAM_ID,
                'name': 'Admin'
            },
            'cases': []
        }
    }

    return all_cases_queue
