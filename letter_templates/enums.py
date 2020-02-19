class Decisions:
    APPROVE = "approve"
    PROVISO = "proviso"
    DENY = "deny"
    NLR = "no_licence_required"

    choices = [
        (APPROVE, "Approve"),
        (PROVISO, "Proviso"),
        (DENY, "Deny"),
        (NLR, "No Licence Required"),
    ]

    @classmethod
    def get_text(cls, choice):
        for key, value in cls.choices:
            if key == choice:
                return value
