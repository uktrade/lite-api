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
        (UK_UNCLASSIFIED, "UK UNCLASSIFIED"),
        (UK_OFFICIAL, "UK OFFICIAL"),
        (UK_OFFICIAL_SENSITIVE, "UK OFFICIAL - SENSITIVE"),
        (UK_SECRET, "UK SECRET"),
        (UK_TOP_SECRET, "UK TOP SECRET"),
        (NATO_UNCLASSIFIED, "NATO UNCLASSIFIED"),
        (NATO_CONFIDENTIAL, "NATO CONFIDENTIAL"),
        (NATO_RESTRICTED, "NATO RESTRICTED"),
        (NATO_SECRET, "NATO SECRET"),
        (OCCAR_UNCLASSIFIED, "OCCAR UNCLASSIFIED"),
        (OCCAR_CONFIDENTIAL, "OCCAR CONFIDENTIAL"),
        (OCCAR_RESTRICTED, "OCCAR RESTRICTED"),
        (OCCAR_SECRET, "OCCAR SECRET"),
    ]

    gov_choices = [
        (UK_UNCLASSIFIED, "UK unclassified"),
        (UK_OFFICIAL, "UK official"),
        (UK_OFFICIAL_SENSITIVE, "UK official - sensitive"),
        (UK_SECRET, "UK secret"),
        (UK_TOP_SECRET, "UK top secret"),
    ]

    @classmethod
    def to_str(cls, obj):
        return [grading[1] for grading in PvGrading.choices if grading[0] == obj][0]
