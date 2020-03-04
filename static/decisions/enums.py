from uuid import UUID


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

    data = {
        APPROVE: UUID("00000000-0000-0000-0000-000000000001"),
        PROVISO: UUID("00000000-0000-0000-0000-000000000002"),
        DENY: UUID("00000000-0000-0000-0000-000000000003"),
        NLR: UUID("00000000-0000-0000-0000-000000000004"),
    }

    @classmethod
    def get_text(cls, choice):
        for key, value in cls.choices:
            if key == choice:
                return value

    @classmethod
    def to_representation(cls):
        return [{"key": decision[0], "value": decision[1]} for decision in cls.choices]
