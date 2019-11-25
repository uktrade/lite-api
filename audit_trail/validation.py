from functools import wraps

from audit_trail.constants import Verb, AuditType
from cases.models import Case
from users.models import GovUser


"""
Use class to handle validation and pass to service?

class Action:
    pass


action = Action(actor=request.user, verb=Verb.ADDED_QUEUES, target=case)

if action.validate():
    audit_service.create(action)
"""


SCHEMAS = {
    AuditType.CASE: {
        'actor': [GovUser],
        'verb': [Verb.ADDED_QUEUES, Verb.REMOVED_QUEUES],
        'action_object': [None],
        'target': [Case],
        'payload': [None, dict]
    },
}


class SchemaException(Exception):
    pass


def _validate_kwargs(**kwargs):
    try:
        """Enforces validation when creating a new audit activity"""
        audit_type = AuditType(kwargs['audit_type'])
        schema = SCHEMAS[audit_type]
    except (ValueError, KeyError):
        raise SchemaException(f'Invalid Audit Type - kwargs: {kwargs}')

    kwarg_schema = {key: value if isinstance(value, Verb) else type(value) for key, value in kwargs.items()}

    for arg, arg_types in schema.items():
        if kwarg_schema.get(arg) not in arg_types:
            raise SchemaException(f'Invalid Audit schema - kwargs: {kwargs}')


def schema_validation(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        _validate_kwargs(**kwargs)
        return func(*args, **kwargs)

    return wrapper
