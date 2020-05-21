from django import template
from django.template.defaultfilters import linebreaksbr

register = template.Library()


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
