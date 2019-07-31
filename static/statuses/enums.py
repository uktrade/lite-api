class CaseStatusEnum:
    """
    This enum is used in this application's `0001_initial` migration file to populate the `statuses_casestatus table`
    If you want to add a status to that table, add it to this enum and specify it's priority list of tuples below
    """
    SUBMITTED = 'submitted'
    MORE_INFORMATION_REQUIRED = 'more_information_required'
    UNDER_REVIEW = 'under_review'
    UNDER_FINAL_REVIEW = 'under_final_review'
    RESUBMITTED = 'resubmitted'
    WITHDRAWN = 'withdrawn'
    APPROVED = 'approved'
    DECLINED = 'declined'

    statuses = [
        (SUBMITTED, 1),
        (RESUBMITTED, 2),
        (MORE_INFORMATION_REQUIRED, 3),
        (UNDER_REVIEW, 4),
        (UNDER_FINAL_REVIEW, 5),
        (WITHDRAWN, 6),
        (APPROVED, 7),
        (DECLINED, 8),
    ]
