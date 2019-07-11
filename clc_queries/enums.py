class ClcQueryStatus:
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
