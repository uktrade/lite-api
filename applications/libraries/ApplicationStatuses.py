from applications.libraries.ChoiceEnum import ChoiceEnum


class ApplicationStatuses(ChoiceEnum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    MORE_INFORMATION_REQUIRED = "More information required"
    UNDER_REVIEW = "Under review"
    RESUBMITTED = "Resubmitted"
    APPROVED = "Approved"
    DECLINED = "Declined"
    WITHDRAWN = "Withdrawn"
