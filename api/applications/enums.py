from enum import Enum
from django.db import models


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


class GoodsStartingPoint:
    choices = [
        ("GB", "Great Britain"),
        ("NI", "Northern Ireland"),
    ]


class GoodsRecipients:
    DIRECT_TO_END_USER = "direct_to_end_user"
    VIA_CONSIGNEE = "via_consignee"
    VIA_CONSIGNEE_AND_THIRD_PARTIES = "via_consignee_and_third_parties"

    choices = [
        (DIRECT_TO_END_USER, "Directly to the end-user"),
        (VIA_CONSIGNEE, "To an end-user via a consignee"),
        (VIA_CONSIGNEE_AND_THIRD_PARTIES, "To an end-user via a consignee, with additional third parties"),
    ]


class GoodsTypeCategory:
    MILITARY = "military"
    CRYPTOGRAPHIC = "cryptographic"
    MEDIA = "media"
    UK_CONTINENTAL_SHELF = "uk_continental_shelf"
    DEALER = "dealer"

    choices = [
        (MILITARY, "Military or dual use"),
        (CRYPTOGRAPHIC, "Cryptographic"),
        (MEDIA, "Media"),
        (UK_CONTINENTAL_SHELF, "UK continental shelf"),
        (DEALER, "Dealer"),
    ]

    # For use in the serialiser
    @classmethod
    def get_text(cls, choice):
        for key, value in cls.choices:
            if key == choice:
                return value

    IMMUTABLE_GOODS = [CRYPTOGRAPHIC, MEDIA, DEALER]
    IMMUTABLE_DESTINATIONS = [CRYPTOGRAPHIC, MEDIA, DEALER, UK_CONTINENTAL_SHELF]


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


class MTCRAnswers:
    CATEGORY_1 = "mtcr_category_1"
    CATEGORY_2 = "mtcr_category_2"
    NO = "none"
    UNKNOWN = "unknown"

    choices = (
        (CATEGORY_1, "MTCR Category 1"),
        (CATEGORY_2, "MTCR Category 2"),
        (NO, "No"),
        (UNKNOWN, "Unknown"),
    )

    @classmethod
    def to_str(cls, obj):
        return next(choice[1] for choice in cls.choices if choice[0] == obj)


class ServiceEquipmentType:
    MOD_FUNDED = "mod_funded"
    PART_MOD_PART_PRIVATE_VENTURE = "part_mod_part_venture"
    PRIVATE_VENTURE = "private_venture"

    choices = (
        (MOD_FUNDED, "MOD funded"),
        (PART_MOD_PART_PRIVATE_VENTURE, "Part MOD part private venture"),
        (PRIVATE_VENTURE, "Private venture"),
    )

    @classmethod
    def to_str(cls, obj):
        return next(choice[1] for choice in cls.choices if choice[0] == obj)

    def to_representation(self):
        return {
            ServiceEquipmentType.MOD_FUNDED: "MOD funded",
            ServiceEquipmentType.PART_MOD_PART_PRIVATE_VENTURE: "Part MOD part private venture",
            ServiceEquipmentType.PRIVATE_VENTURE: "Private venture",
        }[self]


class ContractType:
    NUCLEAR_RELATED = "nuclear_related"
    NAVY = "navy"
    ARMY = "army"
    AIR_FORCE = "air_force"
    POLICE = "police"
    MINISTRY_OF_INTERIOR = "ministry_of_interior"
    OTHER_SECURITY_FORCES = "other_security_forces"
    COMPANIES_NUCLEAR_RELATED = "companies_nuclear_related"
    MARITIME_ANTI_PIRACY = "maritime_anti_piracy"
    AIRCRAFT_MANUFACTURERS = "aircraft_manufacturers"
    REGISTERED_FIREARMS_DEALERS = "registered_firearm_dealers"
    OIL_AND_GAS_INDUSTRY = "oil_and_gas_industry"
    PHARMACEUTICAL_OR_MEDICAL = "pharmaceutical_or_medical"
    MEDIA = "media"
    PRIVATE_MILITARY = "private_military"
    EDUCATION = "education"
    FOR_THE_EXPORTERS_OWN_USE = "for_the_exporters_own_use"
    OTHER_CONTRACT_TYPE = "other_contract_type"

    choices = [
        (NUCLEAR_RELATED, "Nuclear-related (trigger list items)"),
        (NAVY, "Navy"),
        (ARMY, "Army"),
        (AIR_FORCE, "Air force"),
        (POLICE, "Police"),
        (MINISTRY_OF_INTERIOR, "Ministry of Interior (or equivalent)"),
        (OTHER_SECURITY_FORCES, "Other security forces"),
        (COMPANIES_NUCLEAR_RELATED, "Companies requesting Nuclear Trigger List items"),
        (MARITIME_ANTI_PIRACY, "Maritime anti piracy"),
        (AIRCRAFT_MANUFACTURERS, "Aircraft manufacturers, maintainers or operators"),
        (REGISTERED_FIREARMS_DEALERS, "Registered firearm dealers"),
        (OIL_AND_GAS_INDUSTRY, "Oil and gas industry"),
        (PHARMACEUTICAL_OR_MEDICAL, "Pharmaceutical or medical"),
        (MEDIA, "Media"),
        (PRIVATE_MILITARY, "Private military or security companies (including security transportation)"),
        (EDUCATION, "Education (e.g. schools, colleges and universities)"),
        (FOR_THE_EXPORTERS_OWN_USE, "For the exporters own use"),
        (OTHER_CONTRACT_TYPE, "Other contract type"),
    ]

    @classmethod
    def get_text(cls, choice):
        for key, value in cls.choices:
            if key == choice:
                return value

    @classmethod
    def get_flag_name(cls, choice):
        return cls.get_text(choice)[:25]


class ApplicationDocumentType:
    F1686_APPROVAL = "f1686-approval"
    choices = [
        (F1686_APPROVAL, "F1686 approval document"),
    ]

    @classmethod
    def keys(cls):
        return [key for key, _ in cls.choices]


class SecurityClassifiedApprovalsType(models.TextChoices):
    F680 = "F680"
    F1686 = "F1686"
    OTHER = "Other"
