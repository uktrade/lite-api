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
        return [{"key": choice[0], "value": choice[0]} for choice in cls.choices]


class CaseTypeTypeEnum:
    APPLICATION = "application"
    QUERY = "query"

    choices = [
        (APPLICATION, "Application"),
        (QUERY, "Query"),
    ]

    @classmethod
    def as_list(cls):
        return [{"key": choice[0], "value": choice[0]} for choice in cls.choices]


class CaseTypeSubTypeEnum:
    STANDARD = "standard"
    OPEN = "open"
    HMRC = "hmrc"
    EUA = "eua"
    EXHIBITION_CLEARANCE = "exhibition_clearance"
    GIFTING_CLEARANCE = "gifting_clearance"
    F680_CLEARANCE = "f680_clearance"
    GOODS = "goods"

    choices = [
        (STANDARD, "Standard"),
        (OPEN, "Open"),
        (HMRC, "HMRC"),
        (EXHIBITION_CLEARANCE, "Exhibition clearance"),
        (EUA, "End user advisory"),
    ]

    @classmethod
    def as_list(cls):
        return [{"key": choice[0], "value": choice[0]} for choice in cls.choices]

    @classmethod
    def has_parties(cls, application_type):
        """
        Check if the application_type uses parties.
        """
        return application_type in [
            CaseTypeSubTypeEnum.STANDARD,
            CaseTypeSubTypeEnum.HMRC,
            CaseTypeSubTypeEnum.EXHIBITION_CLEARANCE,
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
        sub_type = CaseTypeSubTypeEnum.F680_CLEARANCE

    class EXHC:
        id = UUID("00000000-0000-0000-0000-000000000008")
        reference = CaseTypeReferenceEnum.EXHC
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.EXHIBITION_CLEARANCE

    class GIFT:
        id = UUID("00000000-0000-0000-0000-000000000009")
        reference = CaseTypeReferenceEnum.GIFT
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.GIFTING_CLEARANCE

    class HMRC:
        id = UUID("00000000-0000-0000-0000-000000000010")
        reference = CaseTypeReferenceEnum.CRE
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.HMRC

    class GQY:
        id = UUID("00000000-0000-0000-0000-000000000011")
        reference = CaseTypeReferenceEnum.GQY
        type = CaseTypeTypeEnum.QUERY
        sub_type = CaseTypeSubTypeEnum.GOODS

    class EUA:
        id = UUID("00000000-0000-0000-0000-000000000012")
        reference = CaseTypeReferenceEnum.EUA
        type = CaseTypeTypeEnum.QUERY
        sub_type = CaseTypeSubTypeEnum.EUA

    case_type_list = [OIEL, OGEL, OICL, SIEL, SICL, SITL, F680, EXHC, GIFT, HMRC, GQY, EUA]

    @classmethod
    def case_type_list_to_representation(cls):
        return [{"key": case_type.reference, "value": case_type.reference.upper()} for case_type in cls.case_type_list]

    @classmethod
    def reference_to_id(cls, case_type_reference):
        if not case_type_reference:
            return None
        for case_type in cls.case_type_list:
            if case_type.reference == case_type_reference:
                return case_type.id

    @classmethod
    def references_to_ids(cls, case_type_references) -> list:
        if not case_type_references:
            return []
        return [cls.reference_to_id(case_type_reference) for case_type_reference in case_type_references]


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
