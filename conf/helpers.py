import re


def str_to_bool(v, invert_none=False):
    if v is None:
        if invert_none:
            return True
        return False
    if isinstance(v, bool):
        return v
    return v.lower() in ("yes", "true", "t", "1")


def convert_queryset_to_str(queryset):
    return [str(x) for x in queryset]


def ensure_x_items_not_none(data, x):
    return x == len([item for item in data if item is not None])


def convert_pascal_case_to_snake_case(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def replace_default_string_for_form_select(data, fields, replacement_value=None, default_select_value="blank"):
    """
    lite_forms submodule contains a possible default value for select questions, with a value of 'blank'
    this replaces that default value to None(or expected value) so that the test may give correct serializer errors.
    """
    for field in fields:
        if data.get(field):
            if data[field] == default_select_value:
                data[field] = replacement_value
    return data


def get_value_from_enum(enum, value):
    for choice in enum.choices:
        if choice[0] == value:
            return choice[1]
