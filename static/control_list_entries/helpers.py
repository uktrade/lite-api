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
    data_dict = {control_code["id"]: control_code for control_code in data}
    for control_code in data:
        if control_code["parent_id"] in data_dict:
            parent = data_dict[control_code["parent_id"]]
            if "children" not in parent:
                parent["children"] = []
            parent["children"].append(control_code)

    # Helper function to get all the id's associated with a parent
    def get_list_of_control_code_and_children_ids(control_code):
        id_list = set()
        id_list.add(control_code["id"])
        if "children" in control_code:
            for c in control_code["children"]:
                id_list.update(get_list_of_control_code_and_children_ids(c))
        return id_list

    # Trim the results to have a id only once
    ids = set(data_dict.keys())
    list_of_ultimate_parent_control_codes = []
    for control_code in data_dict.values():
        full_control_code_id_list = get_list_of_control_code_and_children_ids(control_code)
        if ids.intersection(full_control_code_id_list):
            ids = ids.difference(full_control_code_id_list)
            list_of_ultimate_parent_control_codes.append(control_code)

    return list_of_ultimate_parent_control_codes
