from lite_content.lite_api import constants

values = []


def get_string(value):
    def get(d, keys):
        if "." in keys:
            key, rest = keys.split(".", 1)
            return get(d[key], rest)
        else:
            return d[keys]

    return get(values, value)


def get_const_string(value):
    try:
        return getattr(constants, value)
    except AttributeError:
        return ''
