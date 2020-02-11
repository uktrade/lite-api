class CaseTypeEnum:
    class Reference:
        OIEL = "oiel"
        OGEL = "ogel"
        OICL = "oicl"
        SIEL = "siel"
        SICL = "sicl"
        SITL = "sitl"
        F680 = "f680"
        EXHC = "exhc"
        GIFT = "gift"
        CRE = "cre"
        GQY = "gqy"
        EUA = "eua"

        choices = [
            (OIEL, "OIEL"),
            (OGEL, "OGEL"),
            (OICL, "OICL"),
            (SIEL, "SIEL"),
            (SICL, "SICL"),
            (SITL, "SITL"),
            (F680, "F680"),
            (EXHC, "EXHC"),
            (GIFT, "GIFT"),
            (CRE, "CRE"),
            (GQY, "GQY"),
            (EUA, "EUA"),
        ]

        @classmethod
        def as_list(cls):
            return [{"key": choice[0], "value": choice[1]} for choice in cls.choices]

    class Type:
        APPLICATION = "application"
        QUERY = "query"

        choices = [
            (APPLICATION, "Application"),
            (QUERY, "Query"),
        ]

        @classmethod
        def get_text(cls, choice):
            for key, value in cls.choices:
                if key == choice:
                    return value

        @classmethod
        def as_list(cls):
            return [{"key": choice[0], "value": choice[1]} for choice in cls.choices]

    class SubType:
        STANDARD = "standard"
        OPEN = "open"
        HMRC = "hmrc"
        EUA = "eua"
        EXHIBITION_CLEARANCE = "exhibition_clearance"

        choices = [
            (STANDARD, "Standard"),
            (OPEN, "Open"),
            (HMRC, "HMRC"),
            (EXHIBITION_CLEARANCE, "Exhibition clearance"),
            (EUA, "End user advisory"),
        ]

        @classmethod
        def as_list(cls):
            return [{"key": choice[0], "value": choice[1]} for choice in cls.choices]


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
