def str_to_bool(v, invert_none=False):
    if v is None:
        if invert_none:
            return True
        return False
    if isinstance(v, bool):
        return v
    return v.lower() in ('yes', 'true', 't', '1')
