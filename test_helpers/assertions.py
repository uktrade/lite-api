import re

RE_UUID = re.compile('^\w*-\w*-\w*-\w*-\w*$')


def is_uuid_as_string(value):
    return bool(isinstance(value, str) and RE_UUID.match(value))
