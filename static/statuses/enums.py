class CaseStatusEnum:
    APPLICANT_EDITING = "applicant_editing"
    FINALISED = "finalised"
    INITIAL_CHECKS = "initial_checks"
    RESUBMITTED = "resubmitted"
    SUBMITTED = "submitted"
    UNDER_FINAL_REVIEW = "under_final_review"
    UNDER_REVIEW = "under_review"
    WITHDRAWN = "withdrawn"

    choices = [
        (APPLICANT_EDITING, "Applicant editing"),
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
    }

    is_read_only = {
        APPLICANT_EDITING: False,
        FINALISED: True,
        INITIAL_CHECKS: False,
        RESUBMITTED: False,
        SUBMITTED: False,
        UNDER_FINAL_REVIEW: True,
        UNDER_REVIEW: True,
        WITHDRAWN: True,
    }

    @classmethod
    def as_list(cls):
        return [{"status": choice[0], "priority": cls.priority[choice[0]]} for choice in cls.choices]
