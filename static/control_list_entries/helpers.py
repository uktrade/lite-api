from conf.exceptions import NotFoundError
from static.control_list_entries.models import ControlListEntry


def get_control_list_entry(rating):
    try:
        return ControlListEntry.objects.get(rating=rating)
    except ControlListEntry.DoesNotExist:
        raise NotFoundError({"control_list_entry": f"'{rating}' - Control list entry not found"})


def convert_control_list_entries_to_tree(queryset):
    data = queryset.values()

    # Create Parent -> child links using dictionary
    data_dict = {r["id"]: r for r in data}
    for r in data:
        if r["parent_id"] in data_dict:
            parent = data_dict[r["parent_id"]]
            if "children" not in parent:
                parent["children"] = []
            parent["children"].append(r)

    # Helper function to get all the id's associated with a parent
    def get_all_ids(r):
        l = list()
        l.append(r["id"])
        if "children" in r:
            for c in r["children"]:
                l.extend(get_all_ids(c))
        return l

    # Trim the results to have a id only once
    ids = set(data_dict.keys())
    result = []
    for r in data_dict.values():
        the_ids = set(get_all_ids(r))
        if ids.intersection(the_ids):
            ids = ids.difference(the_ids)
            result.append(r)

    return result
