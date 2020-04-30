from datetime import date
from typing import Optional

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied

from audit_trail.enums import AuditType
from audit_trail.models import Audit
from audit_trail.schema import validate_kwargs
from cases.models import Case
from teams.models import Team
from users.enums import UserType
from users.models import ExporterUser, GovUser


@validate_kwargs
def create(actor, verb, action_object=None, target=None, payload=None, ignore_case_status=False):
    if not payload:
        payload = {}

    return Audit.objects.create(
        actor=actor,
        verb=verb.value,
        action_object=action_object,
        target=target,
        payload=payload,
        ignore_case_status=ignore_case_status,
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


def filter_case_activity(
    case_id,
    user_id=None,
    team: Optional[Team] = None,
    user_type: Optional[UserType] = None,
    audit_type: Optional[AuditType] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    note_type=None
):
    case_content_type = ContentType.objects.get_for_model(Case)
    audit_qs = Audit.objects.filter(
        Q(action_object_object_id=case_id, action_object_content_type=case_content_type) |
        Q(target_object_id=case_id, target_content_type=case_content_type)
    )

    if user_id:
        audit_qs = audit_qs.filter(actor_object_id=user_id)

    if team:
        gov_content_type = ContentType.objects.get_for_model(GovUser)
        user_ids = audit_qs.filter(actor_content_type=gov_content_type).values_list("actor_object_id", flat=True)
        team_user_ids = GovUser.objects.filter(id__in=list(user_ids), team=team).values_list("id", flat=True)
        audit_qs = audit_qs.filter(actor_object_id__in=list(team_user_ids))

    if user_type:
        model_cls = {UserType.INTERNAL: GovUser, UserType.EXPORTER: ExporterUser}[user_type]
        user_type_content_type = ContentType.objects.get_for_model(model_cls)
        audit_qs = audit_qs.filter(actor_content_type=user_type_content_type)

    if audit_type:
        audit_qs = audit_qs.filter(verb=audit_type)

    if date_from:
        audit_qs = audit_qs.filter(created_at__date__gte=date_from)

    if date_to:
        audit_qs = audit_qs.filter(created_at__date__lte=date_to)

    return audit_qs
