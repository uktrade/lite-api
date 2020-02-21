from uuid import UUID
from enum import Enum


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


class F680ClearanceTypeEnum:
    MARKET_SURVEY = "market_survey"
    INITIAL_DISCUSSIONS_AND_PROMOTIONS = "initial_discussions_and_promotions"
    DEMONSTRATION_IN_THE_UK_TO_OVERSEAS_CUSTOMERS = "demonstration_uk_overseas_customers"
    DEMONSTRATION_OVERSEAS = "demonstration_overseas"
    TRAINING = "training"
    THROUGH_LIFE_SUPPORT = "through_life_support"

    choices = [
        (MARKET_SURVEY, "Market Survey"),
        (INITIAL_DISCUSSIONS_AND_PROMOTIONS, "Initial discussions and promotions"),
        (DEMONSTRATION_IN_THE_UK_TO_OVERSEAS_CUSTOMERS, "Demonstration in the UK to overseas customers"),
        (DEMONSTRATION_OVERSEAS, "Demonstration overseas"),
        (TRAINING, "Training"),
        (THROUGH_LIFE_SUPPORT, "Through life support"),
    ]

    ids = {
        MARKET_SURVEY: UUID("00000000-0000-0000-0000-000000000001"),
        INITIAL_DISCUSSIONS_AND_PROMOTIONS: UUID("00000000-0000-0000-0000-000000000002"),
        DEMONSTRATION_IN_THE_UK_TO_OVERSEAS_CUSTOMERS: UUID("00000000-0000-0000-0000-000000000003"),
        DEMONSTRATION_OVERSEAS: UUID("00000000-0000-0000-0000-000000000004"),
        TRAINING: UUID("00000000-0000-0000-0000-000000000005"),
        THROUGH_LIFE_SUPPORT: UUID("00000000-0000-0000-0000-000000000006"),
    }
