from uuid import UUID

from conf.helpers import ExtendedEnum


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


class CaseTypeExtendedEnum:
    OIEL = ExtendedEnum.build(
        {
            "id": UUID("00000000-0000-0000-0000-000000000001"),
            "reference": CaseTypeReferenceEnum.OIEL,
            "type": CaseTypeTypeEnum.APPLICATION,
            "sub_type": CaseTypeSubTypeEnum.OPEN,
        }
    )
    OGEL = ExtendedEnum.build(
        {
            "id": UUID("00000000-0000-0000-0000-000000000002"),
            "reference": CaseTypeReferenceEnum.OGEL,
            "type": CaseTypeTypeEnum.APPLICATION,
            "sub_type": CaseTypeSubTypeEnum.OPEN,
        }
    )
    OICL = ExtendedEnum.build(
        {
            "id": UUID("00000000-0000-0000-0000-000000000003"),
            "reference": CaseTypeReferenceEnum.OICL,
            "type": CaseTypeTypeEnum.APPLICATION,
            "sub_type": CaseTypeSubTypeEnum.OPEN,
        }
    )
    SIEL = ExtendedEnum.build(
        {
            "id": UUID("00000000-0000-0000-0000-000000000004"),
            "reference": CaseTypeReferenceEnum.SIEL,
            "type": CaseTypeTypeEnum.APPLICATION,
            "sub_type": CaseTypeSubTypeEnum.STANDARD,
        }
    )
    SICL = ExtendedEnum.build(
        {
            "id": UUID("00000000-0000-0000-0000-000000000005"),
            "reference": CaseTypeReferenceEnum.SICL,
            "type": CaseTypeTypeEnum.APPLICATION,
            "sub_type": CaseTypeSubTypeEnum.STANDARD,
        }
    )
    SITL = ExtendedEnum.build(
        {
            "id": UUID("00000000-0000-0000-0000-000000000006"),
            "reference": CaseTypeReferenceEnum.SITL,
            "type": CaseTypeTypeEnum.APPLICATION,
            "sub_type": CaseTypeSubTypeEnum.STANDARD,
        }
    )
    F680 = ExtendedEnum.build(
        {
            "id": UUID("00000000-0000-0000-0000-000000000007"),
            "reference": CaseTypeReferenceEnum.F680,
            "type": CaseTypeTypeEnum.APPLICATION,
            "sub_type": CaseTypeSubTypeEnum.F680_CLEARANCE,
        }
    )
    EXHC = ExtendedEnum.build(
        {
            "id": UUID("00000000-0000-0000-0000-000000000008"),
            "reference": CaseTypeReferenceEnum.EXHC,
            "type": CaseTypeTypeEnum.APPLICATION,
            "sub_type": CaseTypeSubTypeEnum.EXHIBITION_CLEARANCE,
        }
    )
    GIFT = ExtendedEnum.build(
        {
            "id": UUID("00000000-0000-0000-0000-000000000009"),
            "reference": CaseTypeReferenceEnum.GIFT,
            "type": CaseTypeTypeEnum.APPLICATION,
            "sub_type": CaseTypeSubTypeEnum.GIFTING_CLEARANCE,
        }
    )
    CRE = ExtendedEnum.build(
        {
            "id": UUID("00000000-0000-0000-0000-000000000010"),
            "reference": CaseTypeReferenceEnum.CRE,
            "type": CaseTypeTypeEnum.APPLICATION,
            "sub_type": CaseTypeSubTypeEnum.HMRC,
        }
    )
    GQY = ExtendedEnum.build(
        {
            "id": UUID("00000000-0000-0000-0000-000000000011"),
            "reference": CaseTypeReferenceEnum.GQY,
            "type": CaseTypeTypeEnum.QUERY,
            "sub_type": CaseTypeSubTypeEnum.GOODS,
        }
    )
    EUA = ExtendedEnum.build(
        {
            "id": UUID("00000000-0000-0000-0000-000000000012"),
            "reference": CaseTypeReferenceEnum.EUA,
            "type": CaseTypeTypeEnum.QUERY,
            "sub_type": CaseTypeSubTypeEnum.EUA,
        }
    )

    extended_enums_list = [OIEL, OGEL, OICL, SIEL, SICL, SITL, F680, EXHC, GIFT, CRE, GQY, EUA]

    @classmethod
    def extended_enums_representation(cls):
        return [
            {"key": extended_enum.reference, "value": extended_enum.id} for extended_enum in cls.extended_enums_list
        ]


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
