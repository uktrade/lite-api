from string import Formatter

from api.parties.enums import PartyType
from api.staticdata.statuses.enums import CaseStatusEnum
from lite_content.lite_api import strings


class DefaultValueParameterFormatter(Formatter):
    """String formatter that allows strings to specify a default value
    for substitution parameters. The default is used when the parameter
    is not found in the substitution parameters dictionary (payload).

    Example: "the sky is {colour|blue}"
    Without default: "the sky is {colour}"
    """

    def get_value(self, key, args, kwds):
        if isinstance(key, str):
            try:
                return kwds[key]
            except KeyError:
                try:
                    key, val = key.split("|")
                    try:
                        return kwds[key.strip()]
                    except KeyError:
                        return val.strip()
                except ValueError:
                    raise KeyError(f"Payload does not contain parameter '{key}' and message specifies no default value")
        else:
            return Formatter.get_value(key, args, kwds)


def format_text(format_str, **payload):
    fmt = DefaultValueParameterFormatter()
    text = fmt.format(format_str, **payload)
    if text[-1] not in [":", ".", "?"]:
        text = f"{text}."
    return text


def removed_flags(**payload):
    flags = payload["flag_name"]
    if len(flags) == 1:
        return f"removed the flag '{flags[0]}' from the organisation"
    elif len(flags) >= 2:
        formatted_flags = f"{str(flags[:-1])[1:-1]} and '{flags[-1]}'"
        return f"removed the flags {formatted_flags} from the organisation"


def get_party_type_value(party_type):
    mapping = {
        "end user": PartyType.END_USER,
        "ultimate end user": PartyType.ULTIMATE_END_USER,
        "third party": PartyType.THIRD_PARTY,
        "additional contact": PartyType.ADDITIONAL_CONTACT,
    }
    value = party_type
    if value in mapping:
        value = mapping[party_type]

    return PartyType.get_display_value(value)


def add_party(**payload):
    party_type = payload["party_type"]
    party_type = get_party_type_value(party_type)
    return f"added the {party_type.lower()} {payload['party_name']}"


def remove_party(**payload):
    party_type = payload["party_type"]
    party_type = get_party_type_value(party_type)
    return f"removed the {party_type.lower()} {payload['party_name']}"


def upload_party_document(**payload):
    party_type = PartyType.get_display_value(payload["party_type"])
    return f"uploaded the document {payload['file_name']} for {party_type.lower()} {payload['party_name']}"


def get_updated_status(**payload):
    status = payload.get("status", "").lower()
    if status == CaseStatusEnum.SUBMITTED:
        return "applied for a licence."
    # Default behavior - same as always
    return format_text(strings.Audit.UPDATED_STATUS, **payload)

def product_reviewed(**payload):
    text = f"reviewed the line {payload['line_no']} assessment for {payload['good_name']}\n"

    if payload["old_is_good_controlled"] != payload["new_is_good_controlled"]:
        text += f"Licence required: Changed from '{payload['old_is_good_controlled']}' to '{payload['new_is_good_controlled']}'\n"
    else:
        text += f"Licence required: No change from '{payload['old_is_good_controlled']}'\n"

    if payload["old_control_list_entry"] != payload["new_control_list_entry"]:
        text += f"Control list entry: Changed from '{payload['old_control_list_entry']}' to '{payload['new_control_list_entry']}'\n"
    else:
        text += f"Control list entry: No change from '{payload['old_control_list_entry']}'\n"

    if payload["old_report_summary"] != payload["report_summary"]:
        text += f"Report summary: Changed from '{payload['old_report_summary']}' to '{payload['report_summary']}'"
    else:
        text += f"Report summary: No change from '{payload['old_report_summary']}'"

    return text

def licence_status_updated(**payload):
    status = payload["status"].lower()
    licence = payload["licence"]
    if status == "issued":
        return f"issued licence {licence}."
    elif status == "reinstated":
        return f"reinstated licence {licence}."
    elif status == "cancelled":
        return f"cancelled licence {licence}."
    elif status == "withdrawn":
        return f"withdrew the licence."
