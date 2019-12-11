from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from audit_trail.models import Audit
from audit_trail.schema import validate_kwargs
from audit_trail.serializers import AuditSerializer


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


def get_obj_trail(obj):
    audit_qs = Audit.objects.all()

    obj_as_action_filter = Q(
        action_object_object_id=obj.id,
        action_object_content_type=ContentType.objects.get_for_model(obj)
    )
    obj_as_target_filter = Q(
        target_object_id=obj.id,
        target_content_type=ContentType.objects.get_for_model(obj)
    )

    audit_trail = audit_qs.filter(obj_as_action_filter | obj_as_target_filter)

    serializer = AuditSerializer(audit_trail, many=True)

    return serializer.data
