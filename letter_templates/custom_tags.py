from django import template

register = template.Library()


@register.filter()
def context_data_to_list(data):
    """
    Helper for the test document to output all available data in a readable format
    """
    text = ""

    if isinstance(data, list):
        for item in data:
            text += context_data_to_list(item)
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                text += f"<li><b>{key}:</b>\n<ul>{context_data_to_list(value)}\n</ul>\n</li>"
            elif isinstance(value, list):
                for i in range(len(value)):
                    text += f"<li><b>{key}:</b>\n<ul><li>[item {i}]</li>{context_data_to_list(value[i])}\n</ul>\n</li>"
            elif value:
                text += f"<li><b>{key}:</b> {value}</li>"
    else:
        return data

    return text or "No data for this section"
