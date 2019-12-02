from django.contrib.contenttypes.models import ContentType

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


def get_trail(actor=None, verb=None, action_object=None, target=None):
    qs = Audit.objects.all()

    if actor:
        qs = qs.filter(actor_object_id=actor.id, actor_content_type=ContentType.objects.get_for_model(actor))

    if verb:
        qs = qs.filter(verb=verb)

    if action_object:
        qs = qs.filter(action_object=action_object.id, action_object_content_type=ContentType.objects.get_for_model(action_object))

    if target:
        qs = qs.filter(target_object_id=target.id, target_content_type=ContentType.objects.get_for_model(target))

    return qs
