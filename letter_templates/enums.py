from conf.serializers import KeyValueChoiceField


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

    @classmethod
    def to_representation(cls):
        return [{"key": decision[0], "value": decision[1]} for decision in cls.choices]
