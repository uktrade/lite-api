from conf.exceptions import NotFoundError
from picklist_items.models import PicklistItem


def get_picklist_item(pk):
    try:
        return PicklistItem.objects.get(pk=pk)
    except PicklistItem.DoesNotExist:
        raise NotFoundError({'picklist_item': 'Picklist item not found - ' + str(pk)})
