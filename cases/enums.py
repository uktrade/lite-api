class CaseTypeEnum:
    APPLICATION = "application"
    GOODS_QUERY = "goods_query"
    END_USER_ADVISORY_QUERY = "end_user_advisory_query"
    HMRC_QUERY = "hmrc_query"
    EXHIBITION_CLEARANCE = "exhibition_clearance"
    GIFTING_CLEARANCE = "gifting_clearance"
    F_SIX_EIGHTY_CLEARANCE = "F680_clearance"

    choices = [
        (APPLICATION, "Application"),
        (GOODS_QUERY, "Goods Query"),
        (END_USER_ADVISORY_QUERY, "End User Advisory Query"),
        (HMRC_QUERY, "HMRC Query"),
        (EXHIBITION_CLEARANCE, "MOD Exhibition Clearance"),
        (GIFTING_CLEARANCE, "Gifting Clearance"),
        (F_SIX_EIGHTY_CLEARANCE, "F680 Clearance"),
    ]

    @classmethod
    def get_text(cls, choice):
        for key, value in cls.choices:
            if key == choice:
                return value

    @classmethod
    def as_list(cls):
        return [{"key": choice[0], "value": choice[1],} for choice in cls.choices]


class AdviceType:
    APPROVE = "approve"
    PROVISO = "proviso"
    REFUSE = "refuse"
    NO_LICENCE_REQUIRED = "no_licence_required"
    NOT_APPLICABLE = "not_applicable"
    CONFLICTING = "conflicting"

    choices = [
        (APPROVE, "Approve"),
        (PROVISO, "Proviso"),
        (REFUSE, "Refuse"),
        (NO_LICENCE_REQUIRED, "No Licence Required"),
        (NOT_APPLICABLE, "Not Applicable"),
        (CONFLICTING, "Conflicting"),
    ]


class CaseDocumentState:
    UPLOADED = "UPLOADED"
    GENERATED = "GENERATED"

    choices = [(UPLOADED, "Uploaded"), (GENERATED, "Generated")]
