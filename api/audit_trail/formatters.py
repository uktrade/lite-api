from datetime import datetime
from string import Formatter

from api.cases.enums import AdviceType, CountersignOrder

from api.licences.enums import LicenceStatus
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


def add_flags(**payload):
    flags = [flag.strip() for flag in payload["added_flags"].split(",")]
    if len(flags) == 1:
        return f"added the flag '{flags[0]}'."
    elif len(flags) >= 2:
        formatted_flags = f"{str(flags[:-1])[1:-1]} and '{flags[-1]}'"
        return f"added the flags {formatted_flags}."


def remove_flags(**payload):
    flags = [flag.strip() for flag in payload["removed_flags"].split(",")]
    if len(flags) == 1:
        return f"removed the flag '{flags[0]}'."
    elif len(flags) >= 2:
        formatted_flags = f"{str(flags[:-1])[1:-1]} and '{flags[-1]}'"
        return f"removed the flags {formatted_flags}."


def good_add_flags(**payload):
    flags = [flag.strip() for flag in payload["added_flags"].split(",")]
    good_name = payload["good_name"]
    if len(flags) == 1:
        return f"added the flag '{flags[0]}' from the good '{good_name}'."
    elif len(flags) >= 2:
        formatted_flags = f"{str(flags[:-1])[1:-1]} and '{flags[-1]}'"
        return f"added the flags {formatted_flags} from the good '{good_name}'."


def good_remove_flags(**payload):
    flags = [flag.strip() for flag in payload["removed_flags"].split(",")]
    good_name = payload["good_name"]
    if len(flags) == 1:
        return f"removed the flag '{flags[0]}' from the good '{good_name}'."
    elif len(flags) >= 2:
        formatted_flags = f"{str(flags[:-1])[1:-1]} and '{flags[-1]}'"
        return f"removed the flags {formatted_flags} from the good '{good_name}'."


def good_add_remove_flags(**payload):
    added_flags = [flag.strip() for flag in payload["added_flags"].split(",")]
    removed_flags = [flag.strip() for flag in payload["removed_flags"].split(",")]
    good_name = payload["good_name"]
    if len(added_flags) == 1:
        message = f"added the flag '{added_flags[0]}'"
    elif len(added_flags) >= 2:
        added_formatted_flags = f"{str(added_flags[:-1])[1:-1]} and '{added_flags[-1]}'"
        message = f"added the flags {added_formatted_flags}"

    if len(removed_flags) == 1:
        message += f" and removed the flag '{removed_flags[0]}'"
    elif len(removed_flags) >= 2:
        rem_formatted_flags = f"{str(removed_flags[:-1])[1:-1]} and '{removed_flags[-1]}'"
        message += f" and removed the flags {rem_formatted_flags}"

    message += f" from the good '{good_name}'."
    return message


def destination_add_flags(**payload):
    flags = [flag.strip() for flag in payload["added_flags"].split(",")]
    action = "added"
    destination_name = payload["destination_name"].title()
    return format_flags_message(flags, action, destination_name)


def destination_remove_flags(**payload):
    flags = [flag.strip() for flag in payload["removed_flags"].split(",")]
    # short audit message for LU countersigning case finalising only
    action = "removed"
    is_lu_countersign_finalise_case = payload.get("is_lu_countersign_finalise_case", False)
    if is_lu_countersign_finalise_case:
        return format_flags_message(flags, action)
    else:
        destination_name = payload["destination_name"].title()
        return format_flags_message(flags, action, destination_name)


def format_flags_message(flags, action, destination_name=None):
    number_of_flags = len(flags)

    if number_of_flags == 1:
        message = f"{action} the flag '{flags[0]}'"

    if number_of_flags >= 2:
        all_but_last_flag = ", ".join(f"'{flag}'" for flag in flags[:-1])
        formatted_flags = f"{all_but_last_flag} and '{flags[-1]}'"
        message = f"{action} the flags {formatted_flags}"

    if destination_name and action == "added":
        message += f" to the destination '{destination_name}'"

    if destination_name and action == "removed":
        message += f" from the destination '{destination_name}'"

    message += "."

    return message


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
    return f"added the {party_type.lower()} {payload['party_name']}."


def remove_party(**payload):
    party_type = payload["party_type"]
    party_type = get_party_type_value(party_type)
    return f"removed the {party_type.lower()} {payload['party_name']}."


def upload_party_document(**payload):
    party_type = PartyType.get_display_value(payload["party_type"])
    return f"uploaded the document {payload['file_name']} for {party_type.lower()} {payload['party_name']}."


def get_updated_status(**payload):
    status = payload.get("status", "").lower()
    if status == CaseStatusEnum.SUBMITTED:
        return "applied for a licence."
    if status == CaseStatusEnum.RESUBMITTED:
        return "reapplied for a licence."
    if status == CaseStatusEnum.APPLICANT_EDITING:
        return "is editing their application."
    if status == CaseStatusEnum.REOPENED_FOR_CHANGES:
        return "re-opened the application to changes."
    if status == CaseStatusEnum.WITHDRAWN:
        return "withdrew their application."

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

    if payload.get("old_regime_entries") != payload.get("new_regime_entries"):
        text += f"Regimes: Changed from '{payload['old_regime_entries']}' to '{payload['new_regime_entries']}'\n"
    else:
        text += f"Regimes: No change from '{payload.get('old_regime_entries', 'No regimes')}'\n"

    if payload["old_report_summary"] != payload["report_summary"]:
        text += f"Report summary: Changed from '{payload['old_report_summary']}' to '{payload['report_summary']}'"
    else:
        text += f"Report summary: No change from '{payload['old_report_summary']}'"

    return text


def licence_status_updated(**payload):
    status = payload["status"].lower()
    licence = payload["licence"]
    if status == LicenceStatus.EXHAUSTED:
        return f"The products for licence {licence} were exported and the status set to '{status}'."

    return f"{status} licence {licence}."


def granted_application(**payload):
    start_date = datetime.strptime(payload["start_date"], "%Y-%m-%d").strftime("%-d %B %Y")
    licence_duration = int(payload["licence_duration"])
    if licence_duration > 1:
        return f"issued licence for {licence_duration} months, starting from {start_date}."
    else:
        return f"issued licence for {licence_duration} month, starting from {start_date}."


def reinstated_application(**payload):
    start_date = datetime.strptime(payload["start_date"], "%Y-%m-%d").strftime("%-d %B %Y")
    licence_duration = int(payload["licence_duration"])
    if licence_duration > 1:
        return f"reinstated licence for {licence_duration} months, starting from {start_date}."
    else:
        return f"reinstated licence for {licence_duration} month, starting from {start_date}."


def update_product_usage_data(**payload):
    product_name = payload["product_name"]
    licence_reference = payload["licence_reference"]
    usage = payload["usage"]
    quantity = payload["quantity"]

    single_product_on_licence = quantity == 1 and usage == 1
    exhausted = usage == quantity

    if single_product_on_licence:
        return f"The {product_name} product on licence {licence_reference} was exported."
    elif exhausted:
        return f"All {product_name} products on licence {licence_reference} were exported."
    else:
        # partial export and also default case
        return f"{usage} of {quantity} {product_name} products on licence {licence_reference} were exported."


def create_final_recommendation(**payload):
    decision = payload["decision"]

    if decision == AdviceType.APPROVE:
        return "added a decision of licence approved."
    elif decision == AdviceType.REFUSE:
        return "added a decision of licence refused."
    elif decision == AdviceType.NO_LICENCE_REQUIRED:
        return "added a decision of no licence needed."

    return f"added a decision {decision}."


def generate_decision_letter(**payload):
    decision = payload["decision"]

    if decision == AdviceType.REFUSE:
        return "created a 'licence refused' letter."
    elif decision == AdviceType.NO_LICENCE_REQUIRED:
        return "created a 'no licence required' letter."

    return f"invalid decision {decision} for this event."


def create_lu_advice(advice_type, **payload):
    if advice_type == AdviceType.PROVISO:
        return " added a licence condition."
    return f" added a recommendation to {advice_type}."


def update_lu_advice(advice_type, **payload):
    if advice_type == AdviceType.PROVISO:
        return " edited a licence condition."
    advice_type_noun = {AdviceType.APPROVE: "approval", AdviceType.REFUSE: "refusal"}[advice_type]
    return f" edited their {advice_type_noun} reason."


def lu_countersign_advice(department, order, countersign_accepted, **payload):
    senior_text = "senior " if order == CountersignOrder.SECOND_COUNTERSIGN else ""
    if countersign_accepted:
        return f" {senior_text}countersigned all {department} recommendations."
    return f" declined to {senior_text}countersign {department} recommendations."


def update_lu_meeting_note(advice_type, **payload):
    return " edited their refusal meeting note."


def create_lu_meeting_note(advice_type, **payload):
    return " added a refusal meeting note."
