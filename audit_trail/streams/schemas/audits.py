from collections import namedtuple

from audit_trail.payload import AuditType
from audit_trail.streams.exceptions import AuditSchemaException
from cases.models import Case
from users.models import GovUser, ExporterUser


class Schema(namedtuple("Schema", "actor verb action_object target payload")):
    """
    Schema defines the expected paramaters for generating a streamed audit.
    """

    @classmethod
    def from_kwargs(cls, **kwargs):
        """
        Generates a schema from a set of kwargs.

        Schema:
            actor           - type
            verb            - AuditType
            action_object   - type
            target          - type
            payload         - type

        Any missing keys will be autofilled with None
        verb is a special case that always expects class type AuditType
        """
        missing_kwargs = {}
        for field in Schema._fields:
            if field not in kwargs:
                kwargs[field] = None

        kwarg_schema = {
            key: value if key == "verb" else type(value) if value else None
            for key, value in {**kwargs, **missing_kwargs}.items()
        }
        return Schema(**kwarg_schema)


# List of streamed audit schemas
SCHEMAS = [
    Schema(actor=GovUser, verb=AuditType.UPDATED_STATUS, action_object=None, target=Case, payload=dict),
    Schema(actor=ExporterUser, verb=AuditType.UPDATED_STATUS, action_object=None, target=Case, payload=dict),
    Schema(actor=ExporterUser, verb=AuditType.CREATED, action_object=Case, target=None, payload=dict),
    Schema(actor=GovUser, verb=AuditType.ADD_CASE_OFFICER_TO_CASE, action_object=None, target=Case, payload=dict),
    Schema(actor=GovUser, verb=AuditType.REMOVE_CASE_OFFICER_FROM_CASE, action_object=None, target=Case, payload=dict),
    Schema(
        actor=ExporterUser, verb=AuditType.ADD_COUNTRIES_TO_APPLICATION, action_object=None, target=Case, payload=dict
    ),
    Schema(
        actor=ExporterUser,
        verb=AuditType.REMOVED_COUNTRIES_FROM_APPLICATION,
        action_object=None,
        target=Case,
        payload=dict,
    ),
]


def validate_audit_kwargs(**kwargs):
    """
    Validate the kwargs for creating a streamed audit entry.
    """
    audit_schema = Schema.from_kwargs(**kwargs)

    if audit_schema not in SCHEMAS:
        raise AuditSchemaException
