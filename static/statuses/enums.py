class CaseStatusEnum:
    APPLICANT_EDITING = 'applicant_editing'
    FINALISED = 'finalised'
    INITIAL_CHECKS = 'initial_checks'
    RESUBMITTED = 'resubmitted'
    SUBMITTED = 'submitted'
    UNDER_FINAL_REVIEW = 'under_final_review'
    UNDER_REVIEW = 'under_review'
    WITHDRAWN = 'withdrawn'

    choices = [
        (APPLICANT_EDITING, 'Applicant editing'),
        (FINALISED, 'Finalised'),
        (INITIAL_CHECKS, 'Initial checks'),
        (RESUBMITTED, 'Resubmitted'),
        (SUBMITTED, 'Submitted'),
        (UNDER_FINAL_REVIEW, 'Under final review'),
        (UNDER_REVIEW, 'Under review'),
        (WITHDRAWN, 'Withdrawn'),
    ]
