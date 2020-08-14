from datetime import date
from typing import Optional

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied

from audit_trail.enums import AuditType
from audit_trail.models import Audit
from audit_trail.schema import validate_kwargs
from cases.libraries.dates import make_date_from_params
from api.teams.models import Team
from api.users.enums import UserType
from api.users.enums import SystemUser
from api.users.models import ExporterUser, GovUser, BaseUser


@validate_kwargs
def create(
    actor, verb, action_object=None, target=None, payload=None, ignore_case_status=False, send_notification=True
):
    if not payload:
        payload = {}

    if "additional_text" in payload and not payload["additional_text"]:
        del payload["additional_text"]

    return Audit.objects.create(
        actor=actor,
        verb=verb.value,
        action_object=action_object,
        target=target,
        payload=payload,
        ignore_case_status=ignore_case_status,
        send_notification=send_notification,
    )


@validate_kwargs
def create_system_user_audit(verb, action_object=None, target=None, payload=None, ignore_case_status=False):
    system_user = BaseUser.objects.get(id=SystemUser.id)
    if not payload:
        payload = {}

    return Audit.objects.create(
        actor=system_user,
        verb=verb.value,
        action_object=action_object,
        target=target,
        payload=payload,
        ignore_case_status=ignore_case_status,
    )


def get_activity_for_user_and_model(user, object_type):
    """
    Returns activity data for all objects of the specified model, e.g. all Organisations.
    :param user: Union[GovUser, ExporterUser]
    :param object_type: models.Model
    :return: QuerySet
    """
    if not isinstance(user, (ExporterUser, GovUser)):
        raise PermissionDenied(f"Invalid user object: {type(user)}")

    audit_trail_qs = Audit.objects.all()

    if isinstance(user, ExporterUser):
        # Show exporter-only audit trail.
        audit_trail_qs = audit_trail_qs.filter(actor_content_type=ContentType.objects.get_for_model(ExporterUser))
    obj_content_type = ContentType.objects.get_for_model(object_type)

    obj_as_action_filter = Q(action_object_object_id=object_type.id, action_object_content_type=obj_content_type)
    obj_as_target_filter = Q(target_object_id=object_type.id, target_content_type=obj_content_type)

    audit_trail_qs = audit_trail_qs.filter(obj_as_action_filter | obj_as_target_filter)

    return audit_trail_qs


def filter_object_activity(
    object_id,
    object_content_type,
    user_id=None,
    team: Optional[Team] = None,
    user_type: Optional[UserType] = None,
    audit_type: Optional[AuditType] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """
    Returns filtered activity data for a specific object, identified by the object_id and object_content_type params
    """
    audit_qs = Audit.objects.filter(
        Q(action_object_object_id=object_id, action_object_content_type=object_content_type)
        | Q(target_object_id=object_id, target_content_type=object_content_type)
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
        if audit_type == AuditType.CREATED_CASE_NOTE:
            # Query based on payload additional text rather than type for case notes
            audit_qs = audit_qs.filter(payload__contains="additional_text")
        else:
            audit_qs = audit_qs.filter(verb=audit_type)

    if date_from:
        audit_qs = audit_qs.filter(created_at__date__gte=date_from)

    if date_to:
        audit_qs = audit_qs.filter(created_at__date__lte=date_to)

    return audit_qs


def get_objects_activity_filters(object_id, object_content_type):
    audit_qs = Audit.objects.filter(
        Q(action_object_object_id=object_id, action_object_content_type=object_content_type)
        | Q(target_object_id=object_id, target_content_type=object_content_type)
    )
    activity_types = (
        audit_qs.order_by("verb").exclude(verb=AuditType.CREATED_CASE_NOTE).values_list("verb", flat=True).distinct()
    )
    # Add the created case note audit type if an audit entry exists with additional text
    if audit_qs.filter(payload__contains="additional_text").exists():
        activity_types = list(activity_types)
        activity_types.append(AuditType.CREATED_CASE_NOTE)
        activity_types = sorted(activity_types)
    user_ids = audit_qs.order_by("actor_object_id").values_list("actor_object_id", flat=True).distinct()
    users = BaseUser.objects.filter(id__in=list(user_ids)).values("id", "first_name", "last_name")
    teams = Team.objects.filter(users__id__in=list(user_ids)).order_by("id").values("name", "id").distinct()

    filters = {
        "activity_types": [{"key": verb, "value": AuditType(verb).human_readable()} for verb in activity_types],
        "teams": [{"key": str(team["id"]), "value": team["name"]} for team in teams],
        "user_types": [
            {"key": UserType.INTERNAL.value, "value": UserType.INTERNAL.human_readable()},
            {"key": UserType.EXPORTER.value, "value": UserType.EXPORTER.human_readable()},
        ],
        "users": [{"key": str(user["id"]), "value": f"{user['first_name']} {user['last_name']}"} for user in users],
    }
    return filters


def get_filters(data):
    return {
        "user_id": data.get("user_id"),
        "team": data.get("team_id"),
        "user_type": UserType(data["user_type"]) if data.get("user_type") else None,
        "audit_type": AuditType(data["activity_type"]) if data.get("activity_type") else None,
        "date_from": make_date_from_params("from", data),
        "date_to": make_date_from_params("to", data),
    }
