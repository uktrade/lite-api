class GoodStatus:
    DRAFT = "draft"  # Freshly created good, fully editable
    SUBMITTED = "submitted"  # This good is on use in an application
    QUERY = "query"  # This good is in a Goods Query
    VERIFIED = "verified"  # This good's details have been verified to be correct

    choices = [
        (DRAFT, "Draft"),
        (SUBMITTED, "Submitted"),
        (QUERY, "Goods Query"),
        (VERIFIED, "Verified"),
    ]


class GoodControlled:
    YES = "yes"
    NO = "no"
    UNSURE = "unsure"

    choices = [(YES, "Yes"), (NO, "No"), (UNSURE, "I don't know")]


class GoodPvGraded:
    YES = "yes"
    NO = "no"
    GRADING_REQUIRED = "grading_required"

    choices = [(YES, "Yes"), (NO, "No"), (GRADING_REQUIRED, "Good needs to be graded")]


class PvGrading:
    UK_UNCLASSIFIED = "uk_unclassified"
    UK_OFFICIAL = "uk_official"
    UK_OFFICIAL_SENSITIVE = "uk_official_sensitive"
    UK_SECRET = "uk_secret"  # nosec # noqa
    UK_TOP_SECRET = "uk_top_secret"  # nosec # noqa
    NATO_UNCLASSIFIED = "nato_unclassified"
    NATO_CONFIDENTIAL = "nato_confidential"
    NATO_RESTRICTED = "nato_restricted"
    NATO_SECRET = "nato_secret"  # nosec # noqa
    OCCAR_UNCLASSIFIED = "occar_unclassified"
    OCCAR_CONFIDENTIAL = "occar_confidential"
    OCCAR_RESTRICTED = "occar_restricted"
    OCCAR_SECRET = "occar_secret"  # nosec # noqa

    choices = [
        (UK_UNCLASSIFIED, "UK unclassified"),
        (UK_OFFICIAL, "UK official"),
        (UK_OFFICIAL_SENSITIVE, "UK official - sensitive"),
        (UK_SECRET, "UK secret"),
        (UK_TOP_SECRET, "UK top secret"),
        (NATO_UNCLASSIFIED, "NATO unclassified"),
        (NATO_CONFIDENTIAL, "NATO confidential"),
        (NATO_RESTRICTED, "NATO restricted"),
        (NATO_SECRET, "NATO secret"),
        (OCCAR_UNCLASSIFIED, "OCCAR unclassified"),
        (OCCAR_CONFIDENTIAL, "OCCAR confidential"),
        (OCCAR_RESTRICTED, "OCCAR restricted"),
        (OCCAR_SECRET, "OCCAR secret"),
    ]

    gov_choices = [
        (UK_UNCLASSIFIED, "UK unclassified"),
        (UK_OFFICIAL, "UK official"),
        (UK_OFFICIAL_SENSITIVE, "UK official - sensitive"),
        (UK_SECRET, "UK secret"),
        (UK_TOP_SECRET, "UK top secret"),
    ]
