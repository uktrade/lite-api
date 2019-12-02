from functools import wraps

from audit_trail.constants import Verb
from cases.models import Case, CaseNote
from users.models import GovUser

from collections import namedtuple
"""
Use class to handle validation and pass to service?

class Action:
    pass


action = Action(actor=request.user, verb=Verb.ADDED_QUEUES, target=case)

if action.validate():
    audit_service.create(action)
"""


class Schema(namedtuple('Schema', 'actor verb action_object target payload')):
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
            raise TypeError(f'INVALID KWARGS: {kwargs}')


class Registry:
    __registry = set()

    def check_kwargs(self, **kwargs):
        return self.validate(Schema.from_kwargs(**kwargs))

    def add(self, schema):
        if not isinstance(schema, Schema):
            raise ValueError('[registry]: invalid schema')

        if schema in self.__registry:
            raise ValueError('[schema]: schema already exists')

        self.__registry.add(schema)

    def validate(self, schema):
        return schema in self.__registry


registry = Registry()

# Case activity
for schema in [
    Schema(actor=GovUser, verb=Verb.ADDED_NOTE, action_object=CaseNote, target=Case, payload=dict),
    Schema(actor=GovUser, verb=Verb.REMOVED_NOTE, action_object=CaseNote, target=Case, payload=dict),
    Schema(actor=GovUser, verb=Verb.ADDED_QUEUES, action_object=None, target=Case, payload=dict),
    Schema(actor=GovUser, verb=Verb.REMOVED_QUEUES, action_object=None, target=Case, payload=dict),
]:
    registry.add(schema)


check_kwargs = registry.check_kwargs


def validate_kwargs(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        check_kwargs(**kwargs)
        return func(*args, **kwargs)

    return wrapper
