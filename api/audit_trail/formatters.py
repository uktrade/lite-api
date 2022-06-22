def product_reviewed(**payload):
    text = f"reviewed the line {payload['line_no']} assessment for {payload['good_name']}\n"

    if payload["old_is_good_controlled"] != payload["new_is_good_controlled"]:
        text += f"Licence required: Changed from '{payload['old_is_good_controlled']}'' to '{payload['new_is_good_controlled']}'\n"
    else:
        text += f"Licence required: No change from '{payload['old_is_good_controlled']}'\n"

    if payload["old_control_list_entry"] != payload["new_control_list_entry"]:
        text += f"Control list entry: Changed from '{payload['old_control_list_entry']}'' to '{payload['new_control_list_entry']}'\n"
    else:
        text += f"Control list entry: No change from '{payload['old_control_list_entry']}'\n"

    if payload["old_report_summary"] != payload["report_summary"]:
        text += f"Report summary: Changed from '{payload['old_report_summary']}'' to '{payload['report_summary']}'\n"
    else:
        text += f"Report summary: No change from '{payload['old_report_summary']}'\n"

    return text


def removed_flags(**payload):
    flags = payload["flag_name"]
    if len(flags) == 1:
        return f"removed the flag '{flags[0]}' from the organisation"
    elif len(flags) >= 2:
        formatted_flags = f"{str(flags[:-1])[1:-1]} and '{flags[-1]}'"
        return f"removed the flags {formatted_flags} from the organisation"
