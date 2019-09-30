from conf.exceptions import NotFoundError
from static.control_list_entries.models import ControlListEntry


def get_control_list_entry(rating):
    try:
        return ControlListEntry.objects.get(rating=rating)
    except ControlListEntry.DoesNotExist:
        raise NotFoundError({'control_list_entry': 'Control List Entry Not found'})


def get_control_list_entry_parent_dict(parent):
    if not parent:
        return {}

    return {
        'id': parent.id,
        'rating': parent.rating,
        'text': parent.text,
        'parent': get_control_list_entry_parent_dict(parent.parent)
    }
