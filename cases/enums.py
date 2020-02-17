from uuid import UUID


class CaseTypeReferenceEnum:
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
        (OIEL, "Open Individual Export Licence"),
        (OGEL, "Open General Export Licence"),
        (OICL, "Open Individual Trade Control Licence"),
        (SIEL, "Standard Individual Export Licence"),
        (SICL, "Standard Individual Trade Control Licence"),
        (SITL, "Standard Individual Transhipment Licence"),
        (F680, "MOD F680 Clearance"),
        (EXHC, "MOD Exhibition Clearance"),
        (GIFT, "MOD Gifting Clearance"),
        (CRE, "HMRC Query"),
        (GQY, "Goods Query"),
        (EUA, "End User Advisory Query"),
    ]

    @classmethod
    def as_list(cls):
        return [{"key": choice[0], "value": choice[1]} for choice in cls.choices]


class CaseTypeTypeEnum:
    APPLICATION = "application"
    QUERY = "query"

    choices = [
        (APPLICATION, "Application"),
        (QUERY, "Query"),
    ]

    @classmethod
    def as_list(cls):
        return [{"key": choice[0], "value": choice[1]} for choice in cls.choices]


class CaseTypeSubTypeEnum:
    STANDARD = "standard"
    OPEN = "open"
    HMRC = "hmrc"
    EUA = "end_user_advisory"
    GOODS = "goods"
    EXHIBITION = "exhibition_clearance"
    GIFTING = "gifting_clearance"
    F680 = "f680_clearance"

    choices = [
        (STANDARD, "Standard Licence"),
        (OPEN, "Open Licence"),
        (HMRC, "HMRC Query"),
        (EUA, "End User Advisory Query"),
        (GOODS, "Goods Query"),
        (EXHIBITION, "MOD Exhibition Clearance"),
        (GIFTING, "MOD Gifting Clearance"),
        (F680, "MOD F680 Clearance"),
    ]

    @classmethod
    def as_list(cls):
        return [{"key": choice[0], "value": choice[1]} for choice in cls.choices]

    @classmethod
    def has_parties(cls, application_type):
        """
        Check if the application_type uses parties.
        """
        return application_type in [
            CaseTypeSubTypeEnum.STANDARD,
            CaseTypeSubTypeEnum.HMRC,
            CaseTypeSubTypeEnum.EXHIBITION,
            CaseTypeSubTypeEnum.F680,
            CaseTypeSubTypeEnum.GIFTING,
        ]


class CaseTypeEnum:
    class OIEL:
        id = UUID("00000000-0000-0000-0000-000000000001")
        reference = CaseTypeReferenceEnum.OIEL
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.OPEN

    class OGEL:
        id = UUID("00000000-0000-0000-0000-000000000002")
        reference = CaseTypeReferenceEnum.OGEL
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.OPEN

    class OICL:
        id = UUID("00000000-0000-0000-0000-000000000003")
        reference = CaseTypeReferenceEnum.OICL
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.OPEN

    class SIEL:
        id = UUID("00000000-0000-0000-0000-000000000004")
        reference = CaseTypeReferenceEnum.SIEL
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.STANDARD

    class SICL:
        id = UUID("00000000-0000-0000-0000-000000000005")
        reference = CaseTypeReferenceEnum.SICL
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.STANDARD

    class SITL:
        id = UUID("00000000-0000-0000-0000-000000000006")
        reference = CaseTypeReferenceEnum.SITL
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.STANDARD

    class F680:
        id = UUID("00000000-0000-0000-0000-000000000007")
        reference = CaseTypeReferenceEnum.F680
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.F680

    class EXHIBITION:
        id = UUID("00000000-0000-0000-0000-000000000008")
        reference = CaseTypeReferenceEnum.EXHC
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.EXHIBITION

    class GIFTING:
        id = UUID("00000000-0000-0000-0000-000000000009")
        reference = CaseTypeReferenceEnum.GIFT
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.GIFTING

    class HMRC:
        id = UUID("00000000-0000-0000-0000-000000000010")
        reference = CaseTypeReferenceEnum.CRE
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.HMRC

    class GOODS:
        id = UUID("00000000-0000-0000-0000-000000000011")
        reference = CaseTypeReferenceEnum.GQY
        type = CaseTypeTypeEnum.QUERY
        sub_type = CaseTypeSubTypeEnum.GOODS

    class EUA:
        id = UUID("00000000-0000-0000-0000-000000000012")
        reference = CaseTypeReferenceEnum.EUA
        type = CaseTypeTypeEnum.QUERY
        sub_type = CaseTypeSubTypeEnum.EUA

    case_type_list = [OIEL, OGEL, OICL, SIEL, SICL, SITL, F680, EXHIBITION, GIFTING, HMRC, GOODS, EUA]

    @classmethod
    def case_types_to_representation(cls) -> list:
        return CaseTypeReferenceEnum.as_list()

    @classmethod
    def reference_to_id(cls, case_type_reference):
        if not case_type_reference:
            return None
        for case_type in cls.case_type_list:
            if case_type.reference == case_type_reference:
                return str(case_type.id)

    @classmethod
    def references_to_ids(cls, case_type_references) -> list:
        case_type_ids = []

        if case_type_references:
            for case_type_reference in case_type_references:
                case_type_id = cls.reference_to_id(case_type_reference)
                if case_type_id:
                    case_type_ids.append(case_type_id)

        return case_type_ids


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
