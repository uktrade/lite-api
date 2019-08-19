def str_to_bool(v, invert_none=False):
    if v is None:
        if invert_none:
            return True
        return False
    if isinstance(v, bool):
        return v
    return v.lower() in ('yes', 'true', 't', '1')


def convert_queryset_to_str(queryset):
    return [str(x) for x in queryset]


def ensure_x_items_not_none(data, x):
    return x == len([item for item in data if item is not None])
