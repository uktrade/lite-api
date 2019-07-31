class CaseStatusEnum:
    """
    This enum is used in this application's `0001_initial` migration file to populate the `statuses_casestatus table`
    If you want to add a status to that table, add it to this enum and specify it's priority in the `0001_initial`
    migration file
    """
    SUBMITTED = 'submitted'
    MORE_INFORMATION_REQUIRED = 'more_information_required'
    UNDER_REVIEW = 'under_review'
    UNDER_FINAL_REVIEW = 'under_final_review'
    RESUBMITTED = 'resubmitted'
    WITHDRAWN = 'withdrawn'
    APPROVED = 'approved'
    DECLINED = 'declined'

    choices = [
        (SUBMITTED, 'Submitted'),
        (MORE_INFORMATION_REQUIRED, 'More information required'),
        (UNDER_REVIEW, 'Under review'),
        (UNDER_FINAL_REVIEW, 'Under final review'),
        (RESUBMITTED, 'Resubmitted'),
        (WITHDRAWN, 'Withdrawn'),
        (APPROVED, 'Approved'),
        (DECLINED, 'Declined'),
    ]
