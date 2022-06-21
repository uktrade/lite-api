from api.parties.enums import PartyType


def upload_party_document(**payload):
    party_type = PartyType.get_display_value(payload["party_type"])
    return f"uploaded the document {payload['file_name']} for {party_type.lower()} {payload['party_name']}"
