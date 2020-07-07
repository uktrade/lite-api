class ComplianceVisitTypes:
    FIRST_CONTACT = "first_contact"
    FIRST_VISIT = "first_visit"
    ROUTINE_VISIT = "routine_visit"
    REVISIT = "revisit"

    choices = [
        (FIRST_CONTACT, "First contact"),
        (FIRST_VISIT, "First visit"),
        (ROUTINE_VISIT, "Routine visit"),
        (REVISIT, "Revisit"),
    ]


class ComplianceRiskValues:
    VERY_LOW = "very_low"
    LOWER = "lower"
    MEDIUM = "medium"
    HIGHER = "higher"
    HIGHEST = "highest"

    choices = [
        (VERY_LOW, "Very low risk"),
        (LOWER, "Lower risk"),
        (MEDIUM, "Medium risk"),
        (HIGHER, "Higher risk"),
        (HIGHEST, "Highest risk"),
    ]
