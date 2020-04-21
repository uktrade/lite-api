from audit_trail.payload import AuditType
from audit_trail.streams.exceptions import PayloadSchemaException


def validate(schema, data):
    data_schema = {}

    def generate_data_schema(_schema, _data):
        """
        Recursively generate a key/value dictionary that maps the field name to the data type
        to be used to validate the payload schema.
        """
        for key, value in _data.items():
            if isinstance(value, dict):
                _schema[key] = {}
                generate_data_schema(_schema[key], value)
            else:
                _schema[key] = type(value)

    generate_data_schema(data_schema, data)

    if data_schema != schema:
        raise PayloadSchemaException({"schema": schema, "data": data})


VERB_PAYLOAD_SCHEMAS = {
    AuditType.UPDATED_STATUS: {"status": {"new": str, "old": str}},
    AuditType.ADD_COUNTRIES_TO_APPLICATION: {"countries": list},
    AuditType.REMOVED_COUNTRIES_FROM_APPLICATION: {"countries": list},
    AuditType.ADD_CASE_OFFICER_TO_CASE: {"case_officer": str},
    AuditType.REMOVE_CASE_OFFICER_FROM_CASE: {"case_officer": str},
    AuditType.CREATED: {"status": {"new": str}},
}


def validate_payload(verb, payload):
    """
    Validates the payload of a streamed audit entry
    """
    schema = VERB_PAYLOAD_SCHEMAS[verb]

    validate(schema, payload)
