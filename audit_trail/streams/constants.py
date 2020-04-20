from audit_trail.payload import AuditType


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
