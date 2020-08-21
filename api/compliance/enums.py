# SIEL type compliance cases require a specific control code prefixes. currently: (0 to 9)D, (0 to 9)E, ML21, ML22.
COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES = "(^[0-9][DE].*$)|(^ML21.*$)|(^ML22.*$)"


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

    @classmethod
    def to_str(cls, visit_type):
        return next(choice[1] for choice in cls.choices if choice[0] == visit_type)


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

    @classmethod
    def to_str(cls, risk_value):
        return next(choice[1] for choice in cls.choices if choice[0] == risk_value)
