from api.parties.enums import PartyType


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
