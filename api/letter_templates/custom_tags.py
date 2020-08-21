from django import template
from django.template.defaultfilters import linebreaksbr
from django.utils.safestring import mark_safe

from lite_content.lite_exporter_frontend import strings as exporter_strings

register = template.Library()

STRING_NOT_FOUND_ERROR = "STRING_NOT_FOUND"


@register.filter()
def context_data_to_list(data):
    """
    Helper for the test document to output all available data in a readable format
    """
    text = ""

    if isinstance(data, list):
        for i in range(len(data)):
            text += f"<li>[item {i}]</li>{context_data_to_list(data[i])}"
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                text += f"<li><b>{key}:</b>\n<ul>{context_data_to_list(value)}\n</ul>\n</li>"
            elif isinstance(value, list):
                text += f"<li><b>{key}:</b>\n<ul>"
                if len(value) > 0:
                    for i in range(len(value)):
                        text += f"<li>[item {i}]</li>{context_data_to_list(value[i])}\n"
                else:
                    text += "No data for this section"
                text += f"</ul>\n</li>"
            elif value:
                text += f"<li><b>{key}:</b> {linebreaksbr(value)}</li>"
    else:
        return data

    return text or "No data for this section"


@register.filter()
def default_na(value):
    """
    Returns N/A if the parameter given is none
    """
    if value:
        return value
    else:
        return mark_safe('<span class="govuk-hint govuk-!-margin-0">N/A</span>')  # nosec


@register.filter()
def remove_underscores(value):
    """
    Removes the underscores from a given string
    """
    return value.replace("_", " ").title()


@register.simple_tag(name="exporter_lcs")
@mark_safe
def get_exporter_lite_content_string(value):
    """
    Template tag for accessing constants from the exporter section of LITE content library
    (not for Python use - only HTML)
    """

    def get(object_to_search, nested_properties_list):
        """
        Recursive function used to search an unknown number of nested objects
        for a property. For example if we had a path 'api.cases.CasePage.title' this function
        would take the current object `object_to_search` and get an object called 'CasePage'.
        It would then call itself again to search the 'CasePage' for a property called 'title'.
        :param object_to_search: An unknown object to get the given property from
        :param nested_properties_list: The path list to the attribute we want
        :return: The attribute in the given object for the given path
        """
        object = getattr(object_to_search, nested_properties_list[0])
        if len(nested_properties_list) == 1:
            # We have reached the end of the path and now have the string
            return object.replace("<!--", "<span class='govuk-visually-hidden'>").replace("-->", "</span>")
        else:
            # Search the object for the next property in `nested_properties_list`
            return get(object, nested_properties_list[1:])

    path = value.split(".")
    try:
        # Get initial object from strings.py (may return AttributeError)
        path_object = getattr(exporter_strings, path[0])
        return get(path_object, path[1:]) if len(path) > 1 else path_object
    except AttributeError:
        return STRING_NOT_FOUND_ERROR


@register.filter()
def display_clc_ratings(control_list_entries):
    ratings = [item["rating"] for item in control_list_entries]
    return ", ".join(ratings)
