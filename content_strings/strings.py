import warnings

values = []


def get_string(value):
    warnings.warn(
        "get_string is deprecated. Reference constants from strings directly like strings.CONSTANT_HERE",
        DeprecationWarning,
    )

    def get(d, keys):
        if "." in keys:
            key, rest = keys.split(".", 1)
            return get(d[key], rest)
        else:
            return d[keys]

    return get(values, value)
