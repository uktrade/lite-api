from enum import Enum


class YesNoChoiceType:
    YES = "yes"
    NO = "no"

    yes_no_choices = [
        (YES, "Yes"),
        (NO, "No"),
    ]


class ApplicationExportType:
    PERMANENT = "permanent"
    TEMPORARY = "temporary"

    choices = [
        (PERMANENT, "Permanent"),
        (TEMPORARY, "Temporary"),
    ]


class GoodsCategory:
    ANTI_PIRACY = "anti_piracy"
    MARITIME_ANTI_PIRACY = "maritime_anti_piracy"
    FIREARMS = "firearms"
    INCORPORATED_GOODS = "incorporated_goods"
    choices = [
        (ANTI_PIRACY, "Anti-piracy"),
        (MARITIME_ANTI_PIRACY, "Maritime anti-piracy"),
        (FIREARMS, "Firearms"),
        (INCORPORATED_GOODS, "Incorporated goods"),
    ]

    @classmethod
    def get_text(cls, choice):
        for key, value in cls.choices:
            if key == choice:
                return value


class ApplicationExportLicenceOfficialType:
    YES = "yes"
    NO = "no"

    choices = [
        (YES, "Yes"),
        (NO, "No"),
    ]


class LicenceDuration(Enum):
    """
    Minimum and maximum duration of a granted licence.

    Scale: months
    """

    MIN = 1
    MAX = 999


class DefaultDuration(Enum):
    """
    Default licence durations for different application types.

    TEMPORARY: 1 year
    PERMANENT_STANDARD: 2 years
    PERMANENT_OPEN_EU: 3 years
    PERMANENT_OPEN: 5 years

    Scale: months
    """

    TEMPORARY = 1 * 12
    PERMANENT_STANDARD = 2 * 12
    PERMANENT_OPEN_EU = 3 * 12
    PERMANENT_OPEN = 5 * 12


class MTCRAnswers(Enum):
    CATEGORY_1 = "mtcr_category_1"
    CATEGORY_2 = "mtcr_category_2"
    NO = "none"
    UNKNOWN = "unknown"

    @classmethod
    def choices(cls):
        return (
            (cls.CATEGORY_1.value, cls.CATEGORY_1.to_representation()),
            (cls.CATEGORY_2.value, cls.CATEGORY_2.to_representation()),
            (cls.NO.value, cls.NO.to_representation()),
            (cls.UNKNOWN.value, cls.UNKNOWN.to_representation()),
        )

    def to_representation(self):
        return {
            MTCRAnswers.CATEGORY_1: "MTCR Category 1",
            MTCRAnswers.CATEGORY_2: "MTCR Category 2",
            MTCRAnswers.NO: "No",
            MTCRAnswers.UNKNOWN: "Unknown",
        }[self]


class ServiceEquipmentType(Enum):
    MOD_FUNDED = "mod_funded"
    PART_MOD_PART_PRIVATE_VENTURE = "part_mod_part_venture"
    PRIVATE_VENTURE = "private_venture"

    @classmethod
    def choices(cls):
        return (
            (cls.MOD_FUNDED.value, cls.MOD_FUNDED.to_representation()),
            (cls.PART_MOD_PART_PRIVATE_VENTURE.value, cls.PART_MOD_PART_PRIVATE_VENTURE.to_representation()),
            (cls.PRIVATE_VENTURE.value, cls.PRIVATE_VENTURE.to_representation()),
        )

    def to_representation(self):
        return {
            ServiceEquipmentType.MOD_FUNDED: "MOD funded",
            ServiceEquipmentType.PART_MOD_PART_PRIVATE_VENTURE: "Part MOD part private venture",
            ServiceEquipmentType.PRIVATE_VENTURE: "Private venture",
        }[self]


class TradeControlActivity:
    TRANSFER_OF_GOODS = "transfer_of_goods"
    PROVISION_OF_TRANSPORTATION = "provision_of_transportation"
    PROVISION_OF_FINANCE = "provision_of_finance"
    PROVISION_OF_INSURANCE = "provision_of_insurance"
    PROVISION_OF_ADVERTISING = "provision_of_advertising"
    MARITIME_ANTI_PIRACY = "maritime_anti_piracy"
    OTHER = "other"

    choices = [
        (TRANSFER_OF_GOODS, "Transfer of goods"),
        (PROVISION_OF_TRANSPORTATION, "Transportation services"),
        (PROVISION_OF_FINANCE, "Finance or financial services"),
        (PROVISION_OF_INSURANCE, "Insurance or reinsurance"),
        (PROVISION_OF_ADVERTISING, "General advertising or promotion services"),
        (MARITIME_ANTI_PIRACY, "Maritime anti-piracy"),
        (OTHER, "Other"),
    ]

    @classmethod
    def get_text(cls, choice):
        for key, value in cls.choices:
            if key == choice:
                return value


class TradeControlProductCategory:
    CATEGORY_A = "category_a"
    CATEGORY_B = "category_b"
    CATEGORY_C = "category_c"

    choices = [
        (CATEGORY_A, "Category A"),
        (CATEGORY_B, "Category B"),
        (CATEGORY_C, "Category C"),
    ]

    @classmethod
    def get_text(cls, choice):
        for key, value in cls.choices:
            if key == choice:
                return value
