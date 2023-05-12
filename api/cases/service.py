from django.contrib.contenttypes.models import ContentType
from django.db.models import Min, When, BinaryField, OuterRef, Q

from api.applications.models import CountryOnApplication
from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer
from api.cases.models import Case
from api.flags.enums import FlagStatuses
from api.users.enums import UserType
from api.users.models import BaseUser


def get_destinations(application_id, user_type=None):
    """
    Get destinations for an open application. For gov users they are ordered based on flag priority and alphabetized by name.
    """
    if user_type == UserType.EXPORTER:
        countries_on_application = (
            CountryOnApplication.objects.select_related("country")
            .prefetch_related("flags", "country__flags")
            .filter(application=application_id)
        )
    else:
        countries_on_application = (
            CountryOnApplication.objects.select_related("country")
            .prefetch_related("country__flags", "flags")
            .filter(application=application_id)
            .annotate(
                highest_flag_priority=Min("country__flags__priority"),
                contains_flags=Case(When(country__flags__isnull=True, then=0), default=1, output_field=BinaryField()),
            )
            .order_by("-contains_flags", "highest_flag_priority", "country__name")
        )

    destinations = []

    for coa in countries_on_application:
        destinations.append(
            {
                "id": coa.id,
                "country": {
                    "id": coa.country.id,
                    "name": coa.country.name,
                    "flags": [
                        {"colour": f.colour, "name": f.name, "label": f.label, "id": f.id}
                        for f in coa.country.flags.all()
                        if f.status == FlagStatuses.ACTIVE
                    ],
                },
                "flags": [{"id": f.id, "name": f.name} for f in coa.flags.all()],
                "contract_types": coa.contract_types,
                "other_contract_type_text": coa.other_contract_type_text,
            }
        )

    return {"type": "countries", "data": destinations}


def retrieve_latest_activity(case):
    obj_type = ContentType.objects.get_for_model(Case)
    top_2_per_case = Audit.objects.filter(
        Q(action_object_object_id=OuterRef("action_object_object_id"), action_object_content_type=obj_type)
        | Q(target_object_id=OuterRef("target_object_id"), target_content_type=obj_type)
    ).order_by("-updated_at")[:1]
    activities_qs = Audit.objects.filter(
        Q(id__in=top_2_per_case.values("id")),
        Q(target_object_id=case.id, target_content_type=obj_type)
        | Q(action_object_object_id=case.id, action_object_content_type=obj_type),
    )
    # get users data for activities en bulk to reduce query count
    user_ids = {activity.actor_object_id for activity in activities_qs}
    users = BaseUser.objects.select_related("exporteruser", "govuser", "govuser__team").filter(id__in=user_ids)
    user_map = {str(user.id): user for user in users}
    latest_updates = []
    for activity in activities_qs:
        # prepopulate actor for AuditSerializer
        actor = user_map[activity.actor_object_id]
        if actor.type == UserType.INTERNAL:
            actor = actor.govuser
        elif actor.type == UserType.EXPORTER:
            actor = actor.exporteruser
        activity.actor = actor
        activity_obj = AuditSerializer(activity).data
        latest_updates.append(activity_obj)
    latest_updates = sorted(latest_updates, key=lambda d: d["created_at"], reverse=True)
    return latest_updates[0]
