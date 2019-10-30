class CaseStatusEnum:
    """
    This enum is used in this application's model and `0001_initial` migration file to create and populate the
    `statuses_casestatus table`
    If you want to add a status to that table:
        add it to this enum, specify if status is read-only and it's priority
        run `./manage.py makemigrations`
        add a custom migration step in the generated migration file to populate the
        table with the new data
    (see the `static/statuses/migrations/0003_auto_20191014_1046.py` migration file for an example)
    """
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

    priorities = {
        APPLICANT_EDITING: 2,
        FINALISED: 7,
        INITIAL_CHECKS: 4,
        RESUBMITTED: 3,
        SUBMITTED: 1,
        UNDER_FINAL_REVIEW: 6,
        UNDER_REVIEW: 5,
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
