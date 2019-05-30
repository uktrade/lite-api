class ApplicationStatus:
    SUBMITTED = 'submitted'
    MORE_INFORMATION_REQUIRED = 'more_information_required'
    UNDER_REVIEW = 'under_review'
    RESUBMITTED = 'resubmitted'
    WITHDRAWN = 'withdrawn'
    APPROVED = 'approved'
    DECLINED = 'declined'

    choices = [
        (SUBMITTED, 'Submitted'),
        (MORE_INFORMATION_REQUIRED, 'More information required'),
        (UNDER_REVIEW, 'Under review'),
        (RESUBMITTED, 'Resubmitted'),
        (WITHDRAWN, 'Withdrawn'),
        (APPROVED, 'Approved'),
        (DECLINED, 'Declined'),
    ]


class ApplicationExportType:
    PERMANENT = 'permanent'
    TEMPORARY = 'temporary'

    choices = [
        (PERMANENT, 'Permanent'),
        (TEMPORARY, 'Temporary'),
    ]


class ApplicationLicenceType:
    STANDARD_LICENCE = 'standard_licence'
    OPEN_LICENCE = 'open_licence'

    choices = [
        (STANDARD_LICENCE, 'Standard Individual Export Licence (SIEL)'),
        (OPEN_LICENCE, 'Open Individual Export Licence (OIEL)'),
    ]
