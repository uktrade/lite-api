from audit_trail.models import Audit
from audit_trail.schema import validate_kwargs


@validate_kwargs
def create(actor, verb, action_object=None, target=None, payload=None):
    if not payload:
        payload = {}

    Audit.objects.create(
        actor=actor,
        verb=verb.value,
        action_object=action_object,
        target=target,
        payload=payload,
    )
