from enum import Enum


class ApplicationExportType:
    PERMANENT = "permanent"
    TEMPORARY = "temporary"

    choices = [
        (PERMANENT, "Permanent"),
        (TEMPORARY, "Temporary"),
    ]


class ApplicationType:
    STANDARD_LICENCE = "standard_licence"
    OPEN_LICENCE = "open_licence"
    HMRC_QUERY = "hmrc_query"
    EXHIBITION_CLEARANCE = "exhibition_clearance"

    choices = [
        (STANDARD_LICENCE, "Standard Licence"),
        (OPEN_LICENCE, "Open Licence"),
        (HMRC_QUERY, "HMRC Query"),
        (EXHIBITION_CLEARANCE, "MOD Exhibition Clearance"),
    ]

    @classmethod
    def has_parties(cls, application_type):
        """
        Check if the application_type uses parties.
        """
        return application_type in [
            ApplicationType.STANDARD_LICENCE,
            ApplicationType.HMRC_QUERY,
            ApplicationType.EXHIBITION_CLEARANCE,
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
