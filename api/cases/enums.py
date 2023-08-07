from uuid import UUID

from rest_framework.exceptions import ValidationError

from lite_content.lite_api import strings


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
    OGTCL = "ogtcl"
    OGTL = "ogtl"
    # Compliance cases both require COMP as a prefix in the reference code, so we use an _ to separate the suffix
    #   which means we have both on reference code creation, without affecting filtering case_types etc
    COMP_SITE = "comp_c"
    COMP_VISIT = "comp_v"

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
        (OGTCL, "Open General Trade Control Licence"),
        (OGTL, "Open General Transhipment Licence"),
        (COMP_SITE, "Compliance Site Case"),
        (COMP_VISIT, "Compliance Visit Case"),
    ]

    STANDARD_LICENCES = [SIEL, SICL, SITL]
    OPEN_LICENCES = [OIEL, OICL, OGEL, OGTCL, OGTL]
    MOD_LICENCES = [F680, EXHC, GIFT]

    @classmethod
    def as_list(cls):
        return [{"key": choice[0], "value": choice[1]} for choice in cls.choices]

    @classmethod
    def get_text(cls, status):
        for k, v in cls.choices:
            if status == k:
                return v


class CaseTypeTypeEnum:
    APPLICATION = "application"
    QUERY = "query"
    REGISTRATION = "registration"
    COMPLIANCE = "compliance"

    choices = [
        (APPLICATION, "Application"),
        (QUERY, "Query"),
        (REGISTRATION, "Registration"),
        (COMPLIANCE, "Compliance"),
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
    COMP_SITE = "compliance_site"
    COMP_VISIT = "compliance_visit"

    choices = [
        (STANDARD, "Standard Licence"),
        (OPEN, "Open Licence"),
        (HMRC, "HMRC Query"),
        (EUA, "End User Advisory Query"),
        (GOODS, "Goods Query"),
        (EXHIBITION, "MOD Exhibition Clearance"),
        (GIFTING, "MOD Gifting Clearance"),
        (F680, "MOD F680 Clearance"),
        (COMP_SITE, "Compliance Site Case"),
        (COMP_VISIT, "Compliance Visit Case"),
    ]

    licence = [STANDARD, OPEN, HMRC]
    mod = [F680, EXHIBITION, GIFTING]

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
            CaseTypeSubTypeEnum.OPEN,
            CaseTypeSubTypeEnum.HMRC,
            CaseTypeSubTypeEnum.EXHIBITION,
            CaseTypeSubTypeEnum.F680,
            CaseTypeSubTypeEnum.GIFTING,
            CaseTypeSubTypeEnum.OPEN,
        ]

    @classmethod
    def is_mod_clearance(cls, application_type):
        """
        Check if the application type does not use an export type
        Useful for licence duration
        """
        return application_type in CaseTypeSubTypeEnum.mod


class CaseTypeEnum:
    class OIEL:
        id = UUID("00000000-0000-0000-0000-000000000001")
        reference = CaseTypeReferenceEnum.OIEL
        type = CaseTypeTypeEnum.APPLICATION
        sub_type = CaseTypeSubTypeEnum.OPEN

    class OGEL:
        id = UUID("00000000-0000-0000-0000-000000000002")
        reference = CaseTypeReferenceEnum.OGEL
        type = CaseTypeTypeEnum.REGISTRATION
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

    class OGTCL:
        id = UUID("00000000-0000-0000-0000-000000000013")
        reference = CaseTypeReferenceEnum.OGTCL
        type = CaseTypeTypeEnum.REGISTRATION
        sub_type = CaseTypeSubTypeEnum.OPEN

    class OGTL:
        id = UUID("00000000-0000-0000-0000-000000000014")
        reference = CaseTypeReferenceEnum.OGTL
        type = CaseTypeTypeEnum.REGISTRATION
        sub_type = CaseTypeSubTypeEnum.OPEN

    class COMPLIANCE_SITE:
        id = UUID("00000000-0000-0000-0000-000000000015")
        reference = CaseTypeReferenceEnum.COMP_SITE
        type = CaseTypeTypeEnum.COMPLIANCE
        sub_type = CaseTypeSubTypeEnum.COMP_SITE

    class COMPLIANCE_VISIT:
        id = UUID("00000000-0000-0000-0000-000000000016")
        reference = CaseTypeReferenceEnum.COMP_VISIT
        type = CaseTypeTypeEnum.COMPLIANCE
        sub_type = CaseTypeSubTypeEnum.COMP_VISIT

    CASE_TYPE_LIST = [
        OIEL,
        OGEL,
        OICL,
        SIEL,
        SICL,
        SITL,
        F680,
        EXHIBITION,
        GIFTING,
        HMRC,
        GOODS,
        EUA,
        OGTCL,
        OGTL,
        COMPLIANCE_SITE,
        COMPLIANCE_VISIT,
    ]

    OPEN_GENERAL_LICENCE_IDS = [OGEL.id, OGTCL.id, OGTL.id]
    STANDARD_LICENCE_IDS = [SIEL.id, SICL.id, SITL.id]
    OPEN_LICENCE_IDS = [OIEL.id, OICL.id]
    MOD_LICENCE_IDS = [F680.id, EXHIBITION.id, GIFTING.id]
    LICENCE_IDS = OPEN_GENERAL_LICENCE_IDS + STANDARD_LICENCE_IDS + OPEN_LICENCE_IDS + MOD_LICENCE_IDS

    @classmethod
    def case_types_to_representation(cls):
        return CaseTypeReferenceEnum.as_list()

    @classmethod
    def reference_to_class(cls, case_type_reference):
        if not case_type_reference:
            raise ValidationError({"case_type": [strings.Applications.Generic.SELECT_A_LICENCE_TYPE]})

        for case_type in cls.CASE_TYPE_LIST:
            if case_type.reference == case_type_reference:
                return case_type

    @classmethod
    def reference_to_id(cls, case_type_reference):
        if not case_type_reference:
            return None
        for case_type in cls.CASE_TYPE_LIST:
            if case_type.reference == case_type_reference:
                return str(case_type.id)

    @classmethod
    def references_to_ids(cls, case_type_references):
        case_type_ids = []

        if case_type_references:
            for case_type_reference in case_type_references:
                case_type_id = cls.reference_to_id(case_type_reference)
                if case_type_id:
                    case_type_ids.append(case_type_id)

        return case_type_ids

    @classmethod
    def trade_control_case_type_ids(cls):
        return [cls.SICL.id, cls.OICL.id]


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

    ids = {
        APPROVE: UUID("00000000-0000-0000-0000-000000000001"),
        PROVISO: UUID("00000000-0000-0000-0000-000000000002"),
        REFUSE: UUID("00000000-0000-0000-0000-000000000003"),
        NO_LICENCE_REQUIRED: UUID("00000000-0000-0000-0000-000000000004"),
        NOT_APPLICABLE: UUID("00000000-0000-0000-0000-000000000005"),
        CONFLICTING: UUID("00000000-0000-0000-0000-000000000006"),
        CONFLICTING: UUID("00000000-0000-0000-0000-000000000007"),
    }

    @classmethod
    def get_text(cls, choice):
        for key, value in cls.choices:
            if key == choice:
                return value

    @classmethod
    def to_representation(cls):
        return [{"key": decision[0], "value": decision[1]} for decision in cls.choices]

    @classmethod
    def get_ids(cls, keys):
        return [cls.ids[decision_key] for decision_key in keys]

    @classmethod
    def as_dict(cls):
        return {choice[0]: choice[1] for choice in cls.choices}

    @classmethod
    def as_representation(cls, choice):
        for d in cls.to_representation():
            if d["key"] == choice:
                return d


class AdviceLevel:
    USER = "user"
    TEAM = "team"
    FINAL = "final"

    choices = [
        (USER, "User"),
        (TEAM, "Team"),
        (FINAL, "Final"),
    ]


class CountersignOrder:
    FIRST_COUNTERSIGN = 1
    SECOND_COUNTERSIGN = 2


class CaseDocumentState:
    UPLOADED = "UPLOADED"
    GENERATED = "GENERATED"
    AUTO_GENERATED = "AUTO_GENERATED"

    choices = [(UPLOADED, "Uploaded"), (GENERATED, "Generated"), (AUTO_GENERATED, "Auto Generated")]


class ECJUQueryType:
    ECJU = "ecju_query"
    PRE_VISIT_QUESTIONNAIRE = "pre_visit_questionnaire"
    COMPLIANCE_ACTIONS = "compliance_actions"

    choices = [
        (ECJU, "Standard query"),
        (PRE_VISIT_QUESTIONNAIRE, "Pre-visit question"),
        (COMPLIANCE_ACTIONS, "Compliance action"),
    ]

    @classmethod
    def to_str(cls, obj):
        return next(choice[1] for choice in cls.choices if choice[0] == obj)


class EnforcementXMLEntityTypes:
    APPLICATION = "application"
    END_USER = "end_user"
    CONSIGNEE = "consignee"
    ULTIMATE_END_USER = "ultimate_end_user"
    ADDITIONAL_CONTACT = "additional_contact"
    THIRD_PARTY = "third_party"
    SITE = "site"
    ORGANISATION = "organisation"

    choices = [
        (APPLICATION, "application"),
        (END_USER, "end_user"),
        (CONSIGNEE, "consignee"),
        (ULTIMATE_END_USER, "ultimate_end_user"),
        (THIRD_PARTY, "third_party"),
        (ADDITIONAL_CONTACT, "additional_contact"),
        (SITE, "site"),
        (ORGANISATION, "organisation"),
    ]
