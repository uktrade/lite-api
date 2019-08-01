class CaseStatusEnum:
    """
    This enum is used in this application's `0001_initial` migration file to populate the `statuses_casestatus table`
    If you want to add a status to that table, add it to this enum and specify it's priority list of tuples below
    """
    SUBMITTED = 'Submitted'
    MORE_INFORMATION_REQUIRED = 'More information required'
    UNDER_REVIEW = 'Under review'
    UNDER_FINAL_REVIEW = 'Under final review'
    RESUBMITTED = 'Resubmitted'
    WITHDRAWN = 'Withdrawn'
    APPROVED = 'Approved'
    DECLINED = 'Declined'

    priorities = {
        SUBMITTED: 1,
        RESUBMITTED: 2,
        MORE_INFORMATION_REQUIRED: 3,
        UNDER_REVIEW: 4,
        UNDER_FINAL_REVIEW: 5,
        WITHDRAWN: 6,
        APPROVED: 7,
        DECLINED: 8,
    }
