class CaseStatusEnum:
    APPEAL_FINAL_REVIEW = "appeal_final_review"
    APPEAL_REVIEW = "appeal_review"
    APPLICANT_EDITING = "applicant_editing"
    CHANGE_INTIAL_REVIEW = "change_initial_review"
    CHANGE_UNDER_FINAL_REVIEW = "change_under_final_review"
    CHANGE_UNDER_REVIEW = "change_under_review"
    CLOSED = "closed"
    DEREGISTERED = "de-registered"
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
    UNDER_ECJU_REVIEW = "under_ecju_review"
    UNDER_FINAL_REVIEW = "under_final_review"
    UNDER_REVIEW = "under_review"
    WITHDRAWN = "withdrawn"

    read_only_statuses = [
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

    terminal_statuses = [
        CLOSED,
        DEREGISTERED,
        FINALISED,
        REGISTERED,
        REVOKED,
        SURRENDERED,
        WITHDRAWN
    ]

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
        (UNDER_ECJU_REVIEW, "Under ecju appeal"),
        (UNDER_FINAL_REVIEW, "Under final review"),
        (UNDER_REVIEW, "Under review"),
        (WITHDRAWN, "Withdrawn"),
    ]

    priority = {
        SUBMITTED: 1,
        APPLICANT_EDITING: 2,
        RESUBMITTED: 3,
        INITIAL_CHECKS: 4,
        UNDER_REVIEW: 5,
        UNDER_FINAL_REVIEW: 6,
        FINALISED: 7,
        WITHDRAWN: 8,
        CLOSED: 9,
        REGISTERED: 10,
        UNDER_APPEAL: 11,
        APPEAL_REVIEW: 12,
        APPEAL_FINAL_REVIEW: 13,
        REOPENED_FOR_CHANGES: 14,
        CHANGE_INTIAL_REVIEW: 15,
        CHANGE_UNDER_REVIEW: 16,
        CHANGE_UNDER_FINAL_REVIEW: 17,
        UNDER_ECJU_REVIEW: 18,
        REVOKED: 19,
        SUSPENDED: 20,
        SURRENDERED: 21,
        DEREGISTERED: 22,
    }

    @classmethod
    def is_read_only(cls, status):
        return status in cls.read_only_statuses

    @classmethod
    def is_terminal(cls, status):
        return status in cls.read_only_statuses

    @classmethod
    def as_list(cls):
        return [{"status": choice[0], "priority": cls.priority[choice[0]]} for choice in cls.choices]
