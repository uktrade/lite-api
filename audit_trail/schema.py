from collections import namedtuple
from functools import wraps

from audit_trail.payload import AuditType
from cases.models import Case, CaseNote
from users.models import GovUser


class Schema(namedtuple("Schema", "actor verb action_object target payload")):
    """
    Schema defines a parameter schema for validation.
    """

    @classmethod
    def from_kwargs(cls, **kwargs):
        try:
            missing_kwargs = {}
            for field in Schema._fields:
                if field not in kwargs:
                    kwargs[field] = None

            kwarg_schema = {key: type(value) for key, value in {**kwargs, **missing_kwargs}.items()}
            return Schema(**kwarg_schema)

        except TypeError:
            raise TypeError(f"INVALID KWARGS: {kwargs}")


class Registry:
    """
    Registry holds Audit schemas for validation.
    """

    __registry = set()

    def check_kwargs(self, **kwargs):
        return self.validate(Schema.from_kwargs(**kwargs))

    def add(self, schema):
        if not isinstance(schema, Schema):
            raise ValueError("[registry]: invalid schema")

        if schema in self.__registry:
            raise ValueError("[schema]: schema already exists")

        self.__registry.add(schema)

    def validate(self, schema):
        return schema in self.__registry


registry = Registry()

# Case activity
for schema in [
    Schema(actor=GovUser, verb=AuditType.CREATED_CASE_NOTE, action_object=CaseNote, target=Case, payload=dict),
    Schema(actor=GovUser, verb=AuditType.MOVE_CASE, action_object=None, target=Case, payload=dict),
    Schema(actor=GovUser, verb=AuditType.REMOVE_CASE, action_object=None, target=Case, payload=dict),
]:
    registry.add(schema)


check_kwargs = registry.check_kwargs


def validate_kwargs(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # TODO: compress Verb and activate schema validations.
        # check_kwargs(**kwargs)
        return func(*args, **kwargs)

    return wrapper
