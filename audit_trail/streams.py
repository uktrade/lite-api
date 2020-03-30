from audit_trail.models import Audit
from audit_trail.payload import AuditType
from cases.models import Case
from static.countries.models import Country

STREAMED_AUDITS = [
    AuditType.CREATED.value,
    AuditType.ADD_CASE_OFFICER_TO_CASE.value,
    AuditType.REMOVE_CASE_OFFICER_FROM_CASE.value,
    AuditType.UPDATED_STATUS.value,
    AuditType.ADD_COUNTRIES_TO_APPLICATION.value,
    AuditType.REMOVED_COUNTRIES_FROM_APPLICATION.value
]

TYPE_MAPPING = {
    AuditType.ADD_CASE_OFFICER_TO_CASE: "case_officer",
    AuditType.REMOVE_CASE_OFFICER_FROM_CASE: "case_officer",
    AuditType.UPDATED_STATUS: "status",
    AuditType.ADD_COUNTRIES_TO_APPLICATION: "countries",
    AuditType.REMOVED_COUNTRIES_FROM_APPLICATION: "countries"
}

VERB_MAPPING = {
    AuditType.ADD_CASE_OFFICER_TO_CASE: "add",
    AuditType.REMOVE_CASE_OFFICER_FROM_CASE: "remove",
    AuditType.UPDATED_STATUS: "update",
    AuditType.ADD_COUNTRIES_TO_APPLICATION: "add",
    AuditType.REMOVED_COUNTRIES_FROM_APPLICATION: "remove"
}


PAGE_SIZE = 4


def case_record_json(audit):
    case = audit.target or audit.action_object
    countries = Country.objects.filter(countries_on_application__application=case.id).values_list("name", flat=True)
    return {
        "id": "dit:lite:case:application:{id}:{verb}".format(id=case.id, verb="create"),
        "published": "{ts}".format(ts=case.created_at),
        "object": {
            "type": [
                "dit:lite:case",
                "dit:lite:record",
                "dit:lite:case:application",
            ],
            "id": "dit:lite:case:application:{id}".format(id=case.id),
            "dit:submittedDate": "{ts}".format(ts=case.submitted_at),
            "dit:status": "{status}".format(status=case.status.status),
            "dit:caseOfficer": case.case_officer.email if case.case_officer else "",
            "dit:countries": list(countries)
        },
    }


def case_activity_json(audit):
    case = audit.target
    data_type = TYPE_MAPPING[AuditType(audit.verb)]
    verb = VERB_MAPPING[AuditType(audit.verb)]
    object_data = {
        "type": [
            "dit:lite:case:change",
            "dit:lite:activity",
            "dit:lite:case:change:{data_type}".format(data_type=data_type),
        ],
        "dit:to": {
            "dit:lite:case:{data_type}".format(data_type=data_type): audit.payload[data_type],
        },
        "attributedTo": {
            "id": "dit:lite:case:{case_type}:{id}".format(case_type=case.case_type.sub_type, id=case.id),
        }
    }
    return {
        "id": "dit:lite:case:change:{data_type}:{id}:{audit_id}:{verb}".format(data_type=data_type, id=case.id, audit_id=audit.id, verb=verb),
        "published": "{ts}".format(ts=case.created_at),
        "object": object_data,
    }


def get_stream(n):
    qs = (
        Audit.objects.filter(verb__in=STREAMED_AUDITS)
        .order_by("created_at")
        .prefetch_related("actor", "target", "action_object")
    )[n*PAGE_SIZE: (n+1)*PAGE_SIZE]

    return [
        case_record_json(audit)
        if (isinstance(audit.action_object, Case) or isinstance(audit.target, Case)) and audit.verb == AuditType.CREATED.value
        else case_activity_json(audit)
        for audit in qs
    ]
