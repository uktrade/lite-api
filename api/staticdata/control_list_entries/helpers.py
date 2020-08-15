from api.conf.exceptions import NotFoundError
from api.staticdata.control_list_entries.models import ControlListEntry


def get_control_list_entry(rating):
    try:
        return ControlListEntry.objects.get(rating=rating)
    except ControlListEntry.DoesNotExist:
        raise NotFoundError({"control_list_entry": f"'{rating}' - Control list entry not found"})


def convert_control_list_entries_to_tree(queryset=None):
    # custom queryset exists for testing purposes since it contains a number of random control codes otherwise
    data = queryset if queryset else ControlListEntry.objects.all().values()

    # Link children inside their parent object
    data_dict = {control_code["id"]: control_code for control_code in data}
    for control_code in data:
        # if a control code has a parent, we wish to add it to the parent's "children"
        if control_code["parent_id"]:
            parent = data_dict[control_code["parent_id"]]
            if "children" not in parent:
                parent["children"] = []
            parent["children"].append(control_code)

    # Get a list of items which are are the ultimate parent in their tree. Ignoring any child objects in data_dict
    ultimate_parents_of_tree_list = [data_dict[data["id"]] for data in data_dict.values() if not data["parent_id"]]

    return ultimate_parents_of_tree_list
