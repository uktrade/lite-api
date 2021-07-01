from api.core.exceptions import NotFoundError
from api.staticdata.control_list_entries.models import ControlListEntry


def get_control_list_entry(rating):
    try:
        return ControlListEntry.objects.get(rating=rating)
    except ControlListEntry.DoesNotExist:
        raise NotFoundError({"control_list_entry": f"'{rating}' - Control list entry not found"})


def convert_control_list_entries_to_tree(data):
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


def get_clc_parent_nodes(rating):
    """
    A control list entry can be a group entry or a child of a child entry.
    Given a rating, this function provides the list of all parent nodes in the chain.
    eg.,
    ML1 -> ML1a, ML1b, ML1c, ML1d
    ML1b -> ML1b1, ML1b2
    Given ML1b1, it returns [ML1, ML1b]
    """

    parent_nodes = []
    try:
        node = ControlListEntry.objects.get(rating=rating)
    except ControlListEntry.DoesNotExist:
        node = None

    if node and node.parent:
        parent_nodes.append(node.parent.rating)
        next_parent = get_clc_parent_nodes(node.parent.rating)
        parent_nodes.extend(next_parent)

    return parent_nodes


def get_clc_child_nodes(group_rating):
    """
    A control list entry can have children at multiple nodes.
    Given a group rating, this function provides the list of all child nodes in the chain.
    eg.,
    ML1 -> ML1a, ML1b, ML1c, ML1d
    ML1b -> ML1b1, ML1b2
    Given ML1, it returns [ML1, ML1a, ML1b, ML1b1, ML1b2, ML1c, ML1d]
    """
    child_nodes = []
    try:
        node = ControlListEntry.objects.get(rating=group_rating)
    except ControlListEntry.DoesNotExist:
        node = None

    if node:
        if node.children.exists():
            child_nodes.append(node.rating)
            for child in node.children.all():
                next_children = get_clc_child_nodes(child.rating)
                child_nodes.extend(next_children)
        else:
            child_nodes.append(group_rating)

    return child_nodes
