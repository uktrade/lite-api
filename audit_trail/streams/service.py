"""
MVP activity stream. To be extended appropriately as requirements are drawn up.
"""
import time
from datetime import datetime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone

from applications.models import CountryOnApplication
from audit_trail.models import Audit
from audit_trail.payload import AuditType
from cases.models import Case
from common.models import prefetch_generic_relations

STREAMED_AUDITS = [
    AuditType.CREATED.value,
    AuditType.ADD_CASE_OFFICER_TO_CASE.value,
    AuditType.REMOVE_CASE_OFFICER_FROM_CASE.value,
    AuditType.UPDATED_STATUS.value,
    AuditType.ADD_COUNTRIES_TO_APPLICATION.value,
    AuditType.REMOVED_COUNTRIES_FROM_APPLICATION.value,
]

TYPE_MAPPING = {
    AuditType.ADD_CASE_OFFICER_TO_CASE: "case_officer",
    AuditType.REMOVE_CASE_OFFICER_FROM_CASE: "case_officer",
    AuditType.UPDATED_STATUS: "status",
    AuditType.ADD_COUNTRIES_TO_APPLICATION: "countries",
    AuditType.REMOVED_COUNTRIES_FROM_APPLICATION: "countries",
    AuditType.CREATED: "case",
}

VERB_MAPPING = {
    AuditType.ADD_CASE_OFFICER_TO_CASE: "add",
    AuditType.REMOVE_CASE_OFFICER_FROM_CASE: "remove",
    AuditType.UPDATED_STATUS: "update",
    AuditType.ADD_COUNTRIES_TO_APPLICATION: "add",
    AuditType.REMOVED_COUNTRIES_FROM_APPLICATION: "remove",
    AuditType.CREATED: "create",
}


def case_record_json(case_id, last_created_at, countries):
    """
    Creates an activity stream compatible record for an application.
    A record is only produced for a case with the last activity seen for a case.
    """
    case = Case.objects.select_related("status", "case_officer", "case_type").get(id=case_id)
    return {
        "id": "dit:lite:case:{case_type}:{id}:{verb}".format(
            case_type=case.case_type.sub_type, id=case.id, verb="create"
        ),
        "published": "{ts}".format(ts=last_created_at),
        "object": {
            "type": [
                "dit:lite:case",
                "dit:lite:record",
                "dit:lite:case:{case_type}".format(case_type=case.case_type.sub_type),
            ],
            "id": "dit:lite:case:{case_type}:{id}".format(case_type=case.case_type.sub_type, id=case.id),
            "dit:submittedDate": "{ts}".format(ts=case.submitted_at or ""),
            "dit:status": "{status}".format(status=case.status.status),
            "dit:caseOfficer": case.case_officer.email if case.case_officer else "",
            "dit:countries": countries,
        },
    }


def case_activity_json(audit, case_type):
    """
    Creates an activity stream compatible record for an application activity
    """
    case = audit.target or audit.action_object
    if not case:
        # Some applications in draft status are being deleted
        return {}
    data_type = TYPE_MAPPING[AuditType(audit.verb)]
    verb = VERB_MAPPING[AuditType(audit.verb)]
    object_data = {
        "type": [
            "dit:lite:case:change",
            "dit:lite:activity",
            "dit:lite:case:change:{data_type}".format(data_type=data_type),
        ],
        "attributedTo": {"id": "dit:lite:case:{case_type}:{id}".format(case_type=case_type, id=case.id)},
    }

    # TODO: standardize audit payloads and clean
    if AuditType(audit.verb) == AuditType.CREATED:
        object_data["dit:status"] = case.status.status
        object_data["type"] = [
            "dit:lite:case:create",
            "dit:lite:activity",
        ]
    elif isinstance(audit.payload[data_type], dict):
        if "new" in audit.payload[data_type]:
            object_data["dit:to"] = {
                "dit:lite:case:{data_type}".format(data_type=data_type): audit.payload[data_type]["new"]
            }
        if "old" in audit.payload[data_type]:
            object_data["dit:from"] = {
                "dit:lite:case:{data_type}".format(data_type=data_type): audit.payload[data_type]["old"]
            }
    else:
        object_data["dit:to"] = {"dit:lite:case:{data_type}".format(data_type=data_type): audit.payload[data_type]}

    return {
        "id": "dit:lite:case:change:{data_type}:{id}:{audit_id}:{verb}".format(
            data_type=data_type, id=case.id, audit_id=audit.id, verb=verb
        ),
        "published": "{ts}".format(ts=audit.created_at),
        "object": object_data,
    }


def get_stream(timestamp):
    """
    Returns a paginated stream of activities.
    """
    case_content_type = ContentType.objects.get_for_model(Case)
    audit_qs = Audit.objects.filter(
        Q(action_object_content_type=case_content_type) | Q(target_content_type=case_content_type),
        verb__in=STREAMED_AUDITS,
    ).order_by("created_at")
    if timestamp > 0:
        audit_qs = audit_qs.filter(created_at__gte=timezone.make_aware(datetime.fromtimestamp(timestamp)))
    audit_qs = audit_qs[: settings.STREAM_PAGE_SIZE]

    if not audit_qs:
        return {"data": [], "next_timestamp": None}

    last_created_at = audit_qs[len(audit_qs) - 1].created_at
    timestamp_qs = Audit.objects.filter(verb__in=STREAMED_AUDITS, created_at=last_created_at)

    if timestamp_qs.count() > 1:
        audit_qs = audit_qs | timestamp_qs

    qs = prefetch_generic_relations(audit_qs)

    case_ids = [
        value["target_object_id"] if value["verb"] != AuditType.CREATED.value else value["action_object_object_id"]
        for value in qs.values("target_object_id", "verb", "action_object_object_id")
    ]

    # Prefetch relevant information in bulk to be used for streams
    countries_on_applications = CountryOnApplication.objects.filter(application__id__in=case_ids).values(
        "application_id", "country__name"
    )

    case_types = Case.objects.filter(id__in=case_ids).select_related("case_type").values("id", "case_type__sub_type")
    case_types = {value["id"]: value["case_type__sub_type"] for value in case_types}

    latest_case_audits = (
        Audit.objects.filter(
            target_object_id__in=case_ids,
            target_content_type=ContentType.objects.get_for_model(Case),
            verb__in=STREAMED_AUDITS,
        )
        .order_by("target_object_id", "-created_at")
        .distinct("target_object_id")
        .values_list("id", flat=True)
    )

    # Create stream for each activity
    stream = []

    for audit in qs:
        case_id = audit.target_object_id if audit.verb != AuditType.CREATED.value else audit.action_object_object_id
        data = case_activity_json(audit, case_types[case_id])
        if data:
            stream.append(data)
        if audit.id in latest_case_audits:
            # Only create a case record for last seen activity for a given case.
            countries = [
                d["country__name"] for d in countries_on_applications if d["application_id"] == audit.target_object_id
            ]
            stream.append(case_record_json(audit.target_object_id, audit.created_at, countries))

    return {"data": stream, "next_timestamp": int(time.mktime(last_created_at.timetuple())) + 1}
