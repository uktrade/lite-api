from django.http import Http404

from picklist_items.models import PicklistItem


def get_picklist_item(pk):
    try:
        return PicklistItem.objects.get(pk=pk)
    except PicklistItem.DoesNotExist:
        raise Http404
