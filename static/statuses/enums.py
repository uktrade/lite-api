class CaseStatusEnum:
    APPEAL_FINAL_REVIEW = "appeal_final_review"
    APPEAL_REVIEW = "appeal_review"
    APPLICANT_EDITING = "applicant_editing"
    CHANGE_INTIAL_REVIEW = "change_initial_review"
    CHANGE_UNDER_FINAL_REVIEW = "change_under_final_review"
    CHANGE_UNDER_REVIEW = "change_under_review"
    CLOSED = "closed"
    DEREGISTERED = "deregistered"
    DRAFT = "draft"
    FINALISED = "finalised"
    INITIAL_CHECKS = "initial_checks"
    REGISTERED = "registered"
    REOPENED_FOR_CHANGES = "reopened_for_changes"
    RESUBMITTED = "resubmitted"
    REVOKED = "revoked"
    SUBMITTED = "submitted"
    SURRENDERED = "surrendered"
    SUSPENDED = "suspended"
    UNDER_APPEAL = "under_appeal"
    UNDER_ECJU_REVIEW = "under_ECJU_review"
    UNDER_FINAL_REVIEW = "under_final_review"
    UNDER_REVIEW = "under_review"
    WITHDRAWN = "withdrawn"
    CLC = "clc_review"
    PV = "pv_review"

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
        UNDER_REVIEW,
        UNDER_ECJU_REVIEW,
        UNDER_FINAL_REVIEW,
        REVOKED,
        SURRENDERED,
        SUSPENDED,
        WITHDRAWN,
    ]

    _terminal_statuses = [CLOSED, DEREGISTERED, FINALISED, REGISTERED, REVOKED, SURRENDERED, WITHDRAWN]

    goods_query_statuses = [CLC, PV]

    clc_statuses = [SUBMITTED, CLOSED, WITHDRAWN]

    choices = [
        (APPEAL_FINAL_REVIEW, "Appeal final review"),
        (APPEAL_REVIEW, "Appeal review"),
        (APPLICANT_EDITING, "Applicant editing"),
        (CHANGE_INTIAL_REVIEW, "Change initial review"),
        (CHANGE_UNDER_FINAL_REVIEW, "Change under final review"),
        (CHANGE_UNDER_REVIEW, "Change under review"),
        (CLOSED, "Closed"),
        (DEREGISTERED, "De-registered"),
        (FINALISED, "Finalised"),
        (INITIAL_CHECKS, "Initial checks"),
        (REGISTERED, "Registered"),
        (REOPENED_FOR_CHANGES, "Re-opened for changes"),
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
        (CLC, "CLC review"),
        (PV, "PV grading review"),
    ]

    priority = {
        SUBMITTED: 1,
        APPLICANT_EDITING: 2,
        RESUBMITTED: 3,
        INITIAL_CHECKS: 4,
        UNDER_REVIEW: 5,
        UNDER_FINAL_REVIEW: 6,
        FINALISED: 7,
        CLC: 8,
        PV: 9,
        WITHDRAWN: 10,
        CLOSED: 11,
        REGISTERED: 12,
        UNDER_APPEAL: 13,
        APPEAL_REVIEW: 14,
        APPEAL_FINAL_REVIEW: 15,
        REOPENED_FOR_CHANGES: 16,
        CHANGE_INTIAL_REVIEW: 17,
        CHANGE_UNDER_REVIEW: 18,
        CHANGE_UNDER_FINAL_REVIEW: 19,
        UNDER_ECJU_REVIEW: 20,
        REVOKED: 21,
        SUSPENDED: 22,
        SURRENDERED: 23,
        DEREGISTERED: 24,
    }

    @classmethod
    def get_text(cls, status):
        for k, v in cls.choices:
            if status == k:
                return v

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
    def terminal_statuses(cls):
        return cls._terminal_statuses

    @classmethod
    def as_list(cls):
        from static.statuses.models import CaseStatus
        from static.statuses.serializers import CaseStatusSerializer

        # Exclude the 'Draft' system status
        statuses = CaseStatus.objects.all().order_by("priority").exclude(status="draft")
        return CaseStatusSerializer(statuses, many=True).data
