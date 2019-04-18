def str_to_bool(v):
    if isinstance(v, bool):
        return v
    return v.lower() in ('yes', 'true', 't', '1')
