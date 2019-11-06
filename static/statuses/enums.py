class CaseStatusEnum:
    """
    This enum is used in this application's model and `0001_initial` migration file to create and populate the
    `statuses_casestatus table`
    If you want to add a status to that table:
        add it to this enum, specify its priority in the dictionary below
        run `./manage.py makemigrations`
        add a custom migration step in the generated migration file to populate the
        table with the new data
    (see the `static/statuses/migrations/0003_auto_20191014_1046.py` migration file for an example)
    """

    SUBMITTED = "submitted"
    MORE_INFORMATION_REQUIRED = "more_information_required"
    UNDER_REVIEW = "under_review"
    UNDER_FINAL_REVIEW = "under_final_review"
    RESUBMITTED = "resubmitted"
    WITHDRAWN = "withdrawn"
    FINALISED = "finalised"
    APPLICANT_EDITING = "applicant_editing"

    choices = [
        (SUBMITTED, "Submitted"),
        (MORE_INFORMATION_REQUIRED, "More information required"),
        (UNDER_REVIEW, "Under review"),
        (UNDER_FINAL_REVIEW, "Under final review"),
        (RESUBMITTED, "Resubmitted"),
        (WITHDRAWN, "Withdrawn"),
        (FINALISED, "Finalised"),
        (APPLICANT_EDITING, "Applicant editing"),
    ]

    priorities = {
        SUBMITTED: 1,
        RESUBMITTED: 2,
        MORE_INFORMATION_REQUIRED: 3,
        UNDER_REVIEW: 4,
        UNDER_FINAL_REVIEW: 5,
        WITHDRAWN: 6,
        FINALISED: 7,
        APPLICANT_EDITING: 8,
    }
