from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied

from audit_trail.models import Audit
from audit_trail.schema import validate_kwargs
from users.models import ExporterUser, GovUser


@validate_kwargs
def create(actor, verb, action_object=None, target=None, payload=None):
    if not payload:
        payload = {}

    Audit.objects.create(
        actor=actor, verb=verb.value, action_object=action_object, target=target, payload=payload,
    )


def get_user_obj_trail_qs(user, obj):
    """
    Retrieve audit trail for a Django model object available for a particular user.
    :param user: Union[GovUser, ExporterUser]
    :param obj: models.Model
    :return: QuerySet
    """
    if not isinstance(user, (ExporterUser, GovUser)):
        raise PermissionDenied(f"Invalid user object: {type(user)}")

    audit_trail_qs = Audit.objects.all()

    if isinstance(user, ExporterUser):
        # Show exporter-only audit trail.
        audit_trail_qs = audit_trail_qs.filter(actor_content_type=ContentType.objects.get_for_model(ExporterUser))

    obj_content_type = ContentType.objects.get_for_model(obj)

    obj_as_action_filter = Q(action_object_object_id=obj.id, action_object_content_type=obj_content_type)
    obj_as_target_filter = Q(target_object_id=obj.id, target_content_type=obj_content_type)

    audit_trail_qs = audit_trail_qs.filter(obj_as_action_filter | obj_as_target_filter)

    return audit_trail_qs
