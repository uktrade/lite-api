class CaseStatusEnum:
    APPEAL_FINAL_REVIEW = "appeal_final_review"
    APPEAL_REVIEW = "appeal_review"
    APPLICANT_EDITING = "applicant_editing"
    CHANGE_INTIAL_REVIEW = "change_initial_review"
    CHANGE_UNDER_FINAL_REVIEW = "change_under_final_review"
    CHANGE_UNDER_REVIEW = "change_under_review"
    CLC = "clc_review"
    OPEN = "open"
    UNDER_INTERNAL_REVIEW = "under_internal_review"
    RETURN_TO_INSPECTOR = "return_to_inspector"
    AWAITING_EXPORTER_RESPONSE = "awaiting_exporter_response"
    CLOSED = "closed"
    DEREGISTERED = "deregistered"
    DRAFT = "draft"  # System only status
    FINALISED = "finalised"
    INITIAL_CHECKS = "initial_checks"
    PV = "pv_review"
    REGISTERED = "registered"
    REOPENED_FOR_CHANGES = "reopened_for_changes"
    REOPENED_DUE_TO_ORG_CHANGES = "reopened_due_to_org_changes"
    RESUBMITTED = "resubmitted"
    REVOKED = "revoked"
    OGD_ADVICE = "ogd_advice"
    SUBMITTED = "submitted"
    SURRENDERED = "surrendered"
    SUSPENDED = "suspended"
    UNDER_APPEAL = "under_appeal"
    UNDER_ECJU_REVIEW = "under_ECJU_review"
    UNDER_FINAL_REVIEW = "under_final_review"
    UNDER_REVIEW = "under_review"
    WITHDRAWN = "withdrawn"

    _system_status = [DRAFT]

    _read_only_statuses = [
        APPEAL_REVIEW,
        APPEAL_FINAL_REVIEW,
        CHANGE_UNDER_REVIEW,
        CHANGE_UNDER_FINAL_REVIEW,
        CLOSED,
        DEREGISTERED,
        FINALISED,
        REGISTERED,
        REOPENED_DUE_TO_ORG_CHANGES,
        UNDER_REVIEW,
        UNDER_ECJU_REVIEW,
        UNDER_FINAL_REVIEW,
        REVOKED,
        SURRENDERED,
        SUSPENDED,
        WITHDRAWN,
        OGD_ADVICE,
    ]

    _major_editable_statuses = [APPLICANT_EDITING, DRAFT]

    _terminal_statuses = [CLOSED, DEREGISTERED, FINALISED, REGISTERED, REVOKED, SURRENDERED, WITHDRAWN]

    goods_query_statuses = [CLC, PV]

    clc_statuses = [SUBMITTED, CLOSED, WITHDRAWN]

    compliance_site_statuses = [OPEN, CLOSED]

    compliance_visit_statuses = [OPEN, UNDER_INTERNAL_REVIEW, RETURN_TO_INSPECTOR, AWAITING_EXPORTER_RESPONSE, CLOSED]

    choices = [
        (APPEAL_FINAL_REVIEW, "Appeal final review"),
        (APPEAL_REVIEW, "Appeal review"),
        (APPLICANT_EDITING, "Applicant editing"),
        (CHANGE_INTIAL_REVIEW, "Change initial review"),
        (CHANGE_UNDER_FINAL_REVIEW, "Change under final review"),
        (CHANGE_UNDER_REVIEW, "Change under review"),
        (CLC, "CLC review"),
        (OPEN, "Open"),
        (UNDER_INTERNAL_REVIEW, "Under internal review"),
        (RETURN_TO_INSPECTOR, "Return to inspector"),
        (AWAITING_EXPORTER_RESPONSE, "Awaiting exporter response"),
        (CLOSED, "Closed"),
        (DEREGISTERED, "De-registered"),
        (FINALISED, "Finalised"),
        (INITIAL_CHECKS, "Initial checks"),
        (PV, "PV grading review"),
        (REGISTERED, "Registered"),
        (REOPENED_FOR_CHANGES, "Re-opened for changes"),
        (REOPENED_DUE_TO_ORG_CHANGES, "Re-opened due to org changes"),
        (RESUBMITTED, "Resubmitted"),
        (REVOKED, "Revoked"),
        (SUBMITTED, "Submitted"),
        (SURRENDERED, "Surrendered"),
        (SUSPENDED, "Suspended"),
        (UNDER_APPEAL, "Under appeal"),
        (UNDER_ECJU_REVIEW, "Under ECJU appeal"),
        (UNDER_FINAL_REVIEW, "Under final review"),
        (UNDER_REVIEW, "Under review"),
        (WITHDRAWN, "Withdrawn"),
        (OGD_ADVICE, "OGD Advice"),
    ]

    priority = {
        SUBMITTED: 1,
        APPLICANT_EDITING: 2,
        RESUBMITTED: 3,
        INITIAL_CHECKS: 4,
        UNDER_REVIEW: 5,
        OGD_ADVICE: 6,
        UNDER_FINAL_REVIEW: 7,
        FINALISED: 8,
        CLC: 9,
        PV: 10,
        OPEN: 11,
        UNDER_INTERNAL_REVIEW: 12,
        RETURN_TO_INSPECTOR: 13,
        AWAITING_EXPORTER_RESPONSE: 14,
        WITHDRAWN: 15,
        CLOSED: 16,
        REGISTERED: 17,
        UNDER_APPEAL: 18,
        APPEAL_REVIEW: 19,
        APPEAL_FINAL_REVIEW: 20,
        REOPENED_FOR_CHANGES: 21,
        REOPENED_DUE_TO_ORG_CHANGES: 22,
        CHANGE_INTIAL_REVIEW: 23,
        CHANGE_UNDER_REVIEW: 24,
        CHANGE_UNDER_FINAL_REVIEW: 25,
        UNDER_ECJU_REVIEW: 26,
        REVOKED: 27,
        SUSPENDED: 28,
        SURRENDERED: 29,
        DEREGISTERED: 30,
    }

    @classmethod
    def get_text(cls, status):
        # All available statuses and DRAFT (System only status)
        for k, v in [*cls.choices, (cls.DRAFT, "Draft")]:
            if status == k:
                return v

    @classmethod
    def get_value(cls, status):
        # All available statuses and DRAFT (System only status)
        for k, v in [*cls.choices, (cls.DRAFT, "Draft")]:
            if status == v:
                return k

    @classmethod
    def is_read_only(cls, status):
        return status in cls._read_only_statuses

    @classmethod
    def is_terminal(cls, status):
        return status in cls._terminal_statuses

    @classmethod
    def is_system_status(cls, status):
        return status in cls._system_status

    @classmethod
    def read_only_statuses(cls):
        return cls._read_only_statuses

    @classmethod
    def major_editable_statuses(cls):
        return cls._major_editable_statuses

    @classmethod
    def terminal_statuses(cls):
        return cls._terminal_statuses

    @classmethod
    def as_list(cls):
        from static.statuses.models import CaseStatus
        from static.statuses.serializers import CaseStatusSerializer

        # Exclude the 'Draft' system status
        statuses = CaseStatus.objects.all().order_by("priority").exclude(status="draft")
        return CaseStatusSerializer(statuses, many=True).data
