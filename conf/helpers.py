import datetime
import re

from django.templatetags.tz import do_timezone
from django.utils import timezone
from pytz import timezone as get_timezone


DATE_FORMAT = "%d %B %Y"
TIME_FORMAT = "%H:%M"


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


def convert_pascal_case_to_snake_case(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def get_value_from_enum(value, enum):
    for choice in enum.choices:
        if choice[0] == value:
            return choice[1]


def convert_date_to_string(value):
    return_value = do_timezone(datetime.datetime.strptime(str(value), "%Y-%m-%d"), "Europe/London")
    return return_value.strftime("%d %B " "%Y")


def date_to_drf_date(date):
    """
    Given a date, returns a correctly formatted string instance of it
    suitable for comparison to rest framework datetimes
    """
    return date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def friendly_boolean(boolean):
    """
    Returns 'Yes' if boolean is True, 'No' if boolean is False and None otherwise
    """
    if boolean is None or boolean == "":
        return None
    elif boolean is True or str(boolean).lower() == "true":
        return "Yes"
    else:
        return "No"


def pluralise_unit(unit, value):
    """
    Modify units given from the API to include an 's' if the
    value is not singular.

    Units require an (s) at the end of their names to
    use this functionality.
    """
    is_singular = value == "1"

    if "(s)" in unit:
        if is_singular:
            return unit.replace("(s)", "")
        else:
            return unit.replace("(s)", "s")

    return unit


def get_local_datetime():
    utc = timezone.now()
    return utc.astimezone(get_timezone("Europe/London"))


def get_date_and_time():
    now = get_local_datetime()
    return now.strftime(DATE_FORMAT), now.strftime(TIME_FORMAT)


def add_months(start_date, months, date_format=DATE_FORMAT):
    year = start_date.year
    month = start_date.month

    for _ in range(months):
        month += 1
        if month == 13:
            year += 1
            month = 1

    new_date = datetime.date(year=year, month=month, day=start_date.day)
    return new_date.strftime(date_format)
