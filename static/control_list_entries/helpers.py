from conf.exceptions import NotFoundError
from static.control_list_entries.models import ControlRating


def get_rating(rating):
    try:
        return ControlRating.objects.get(rating=rating)
    except ControlRating.DoesNotExist:
        raise NotFoundError({'control_rating': 'Control Rating Not found'})


def get_parent(parent):
    if not parent:
        return {}

    return {
        'id': parent.id,
        'rating': parent.rating,
        'text': parent.text,
        'parent': get_parent(parent.parent)
    }
