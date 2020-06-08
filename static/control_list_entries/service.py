from common.cache import lite_cache, Key
from static.control_list_entries.models import ControlListEntry


@lite_cache(Key.CONTROL_LIST_ENTRIES_LIST)
def control_list_entries_list():
    return list(ControlListEntry.objects.all().values())
