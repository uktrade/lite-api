class CaseStatusEnum:
    APPLICANT_EDITING = "applicant_editing"
    CLOSED = "closed"
    FINALISED = "finalised"
    INITIAL_CHECKS = "initial_checks"
    RESUBMITTED = "resubmitted"
    SUBMITTED = "submitted"
    UNDER_FINAL_REVIEW = "under_final_review"
    UNDER_REVIEW = "under_review"
    WITHDRAWN = "withdrawn"

    read_only_statuses = [CLOSED, FINALISED, UNDER_REVIEW, UNDER_FINAL_REVIEW, WITHDRAWN]
    terminal_statuses = [CLOSED, FINALISED, WITHDRAWN]

    choices = [
        (APPLICANT_EDITING, "Applicant editing"),
        (CLOSED, "Closed"),
        (FINALISED, "Finalised"),
        (INITIAL_CHECKS, "Initial checks"),
        (RESUBMITTED, "Resubmitted"),
        (SUBMITTED, "Submitted"),
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
