"""
MVP activity stream. To be extended appropriately as requirements are drawn up.
"""
from django.conf import settings

from audit_trail.models import Audit
from audit_trail.payload import AuditType
from common.models import prefetch_generic_relations
from static.countries.models import Country

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
}

VERB_MAPPING = {
    AuditType.ADD_CASE_OFFICER_TO_CASE: "add",
    AuditType.REMOVE_CASE_OFFICER_FROM_CASE: "remove",
    AuditType.UPDATED_STATUS: "update",
    AuditType.ADD_COUNTRIES_TO_APPLICATION: "add",
    AuditType.REMOVED_COUNTRIES_FROM_APPLICATION: "remove",
}


def case_record_json(audit):
    """
    Creates an activity stream compatible record for an application
    """
    case = audit.action_object or audit.target
    if case is None:
        # Some applications in draft status are being deleted
        return {}
    countries = Country.objects.filter(countries_on_application__application=case.id).values_list("name", flat=True)
    return {
        "id": "dit:lite:case:application:{id}:{verb}".format(id=case.id, verb="create"),
        "published": "{ts}".format(ts=case.created_at),
        "object": {
            "type": ["dit:lite:case", "dit:lite:record", "dit:lite:case:application",],
            "id": "dit:lite:case:application:{id}".format(id=case.id),
            "dit:submittedDate": "{ts}".format(ts=case.submitted_at or ""),
            "dit:status": "{status}".format(status=case.status.status),
            "dit:caseOfficer": case.case_officer.email if case.case_officer else "",
            "dit:countries": list(countries),
        },
    }


def case_activity_json(audit):
    """
    Creates an activity stream compatible record for an application activity
    """
    case = audit.target
    if case is None:
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
        "dit:to": {"dit:lite:case:{data_type}".format(data_type=data_type): audit.payload[data_type],},
        "attributedTo": {"id": "dit:lite:case:{case_type}:{id}".format(case_type=case.case_type.sub_type, id=case.id),},
    }
    return {
        "id": "dit:lite:case:change:{data_type}:{id}:{audit_id}:{verb}".format(
            data_type=data_type, id=case.id, audit_id=audit.id, verb=verb
        ),
        "published": "{ts}".format(ts=audit.created_at),
        "object": object_data,
    }


def get_stream(n):
    """
    Returns a paginated stream of activities.
    """
    PAGE_SIZE = settings.STREAM_PAGE_SIZE

    qs = prefetch_generic_relations(
        Audit.streams.filter(verb__in=STREAMED_AUDITS).order_by("created_at")[n * PAGE_SIZE : (n + 1) * PAGE_SIZE]
    )

    stream = []

    for audit in qs:
        data = case_record_json(audit) if audit.verb == AuditType.CREATED.value else case_activity_json(audit)
        if data:
            stream.append(data)

    return stream
