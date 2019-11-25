from actstream import action

from audit_trail.validation import schema_validation


@schema_validation
def create(audit_type, actor, verb, action_object=None, target=None, payload=None):
    if not payload:
        payload = {}

    action.send(
        actor,
        verb=verb.value,
        action_object=action_object,
        target=target,
        payload=payload,
        audit_type=audit_type.value
    )
