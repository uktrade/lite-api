from django.db import models


class GoodStatus:
    DRAFT = "draft"  # Freshly created good, fully editable
    SUBMITTED = "submitted"  # This good is on use in an application
    QUERY = "query"  # This good is in a Goods Query
    VERIFIED = "verified"  # This good's details have been verified to be correct

    choices = [
        (DRAFT, "Draft"),
        (SUBMITTED, "Submitted"),
        (QUERY, "Goods Query"),
        (VERIFIED, "Verified"),
    ]


class ItemType:
    EQUIPMENT = "equipment"
    MODEL = "model"
    DATASHEET = "datasheet"
    BROCHURE = "brochure"
    VIDEO = "video"
    OTHER = "other"

    choices = [
        (EQUIPMENT, "Equipment"),
        (MODEL, "Model"),
        (DATASHEET, "Datasheet"),
        (BROCHURE, "Brochure"),
        (VIDEO, "Video"),
        (OTHER, "Other"),
    ]


class GoodControlled:
    choices = [
        (True, "Yes"),
        (False, "No"),
        (None, "I don't know"),
    ]

    @classmethod
    def to_str(cls, obj):
        return next(choice[1] for choice in cls.choices if choice[0] == obj) if obj else None


class GoodPvGraded:
    YES = "yes"
    NO = "no"
    GRADING_REQUIRED = "grading_required"

    choices = [
        (YES, "Yes"),
        (NO, "No"),
        (GRADING_REQUIRED, "Good needs to be graded"),
    ]

    @classmethod
    def to_str(cls, option):
        return next(choice[1] for choice in cls.choices if choice[0] == option)


class PvGrading:
    UK_UNCLASSIFIED = "uk_unclassified"
    UK_OFFICIAL = "uk_official"
    UK_OFFICIAL_SENSITIVE = "uk_official_sensitive"
    UK_SECRET = "uk_secret"  # nosec # noqa
    UK_TOP_SECRET = "uk_top_secret"  # nosec # noqa
    NATO_UNCLASSIFIED = "nato_unclassified"
    NATO_CONFIDENTIAL = "nato_confidential"
    NATO_RESTRICTED = "nato_restricted"
    NATO_SECRET = "nato_secret"  # nosec # noqa
    OCCAR_UNCLASSIFIED = "occar_unclassified"
    OCCAR_CONFIDENTIAL = "occar_confidential"
    OCCAR_RESTRICTED = "occar_restricted"
    OCCAR_SECRET = "occar_secret"  # nosec # noqa
    UNCLASSIFIED = "unclassified"
    OFFICIAL = "official"
    OFFICIAL_SENSITIVE = "official-sensitive"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"  # nosec # noqa
    TOP_SECRET = "top secret"  # nosec # noqa

    choices = [
        (UK_UNCLASSIFIED, "UK UNCLASSIFIED"),
        (UK_OFFICIAL, "UK OFFICIAL"),
        (UK_OFFICIAL_SENSITIVE, "UK OFFICIAL - SENSITIVE"),
        (UK_SECRET, "UK SECRET"),
        (UK_TOP_SECRET, "UK TOP SECRET"),
        (NATO_UNCLASSIFIED, "NATO UNCLASSIFIED"),
        (NATO_CONFIDENTIAL, "NATO CONFIDENTIAL"),
        (NATO_RESTRICTED, "NATO RESTRICTED"),
        (NATO_SECRET, "NATO SECRET"),
        (OCCAR_UNCLASSIFIED, "OCCAR UNCLASSIFIED"),
        (OCCAR_CONFIDENTIAL, "OCCAR CONFIDENTIAL"),
        (OCCAR_RESTRICTED, "OCCAR RESTRICTED"),
        (OCCAR_SECRET, "OCCAR SECRET"),
    ]

    choices_new = [
        (UNCLASSIFIED, "Unclassified"),
        (OFFICIAL, "Official"),
        (OFFICIAL_SENSITIVE, "Official-sensitive"),
        (RESTRICTED, "Restricted"),
        (CONFIDENTIAL, "Confidential"),
        (SECRET, "Secret"),
        (TOP_SECRET, "Top secret"),
    ]

    gov_choices = [
        (UK_UNCLASSIFIED, "UK unclassified"),
        (UK_OFFICIAL, "UK official"),
        (UK_OFFICIAL_SENSITIVE, "UK official - sensitive"),
        (UK_SECRET, "UK secret"),
        (UK_TOP_SECRET, "UK top secret"),
    ]

    @classmethod
    def to_str(cls, obj):
        return next(choice[1] for choice in (cls.choices + cls.choices_new) if choice[0] == obj) if obj else None


class ItemCategory:
    GROUP1_PLATFORM = "group1_platform"
    GROUP1_DEVICE = "group1_device"
    GROUP1_COMPONENTS = "group1_components"
    GROUP1_MATERIALS = "group1_materials"
    GROUP2_FIREARMS = "group2_firearms"
    GROUP3_SOFTWARE = "group3_software"
    GROUP3_TECHNOLOGY = "group3_technology"

    choices = [
        (GROUP1_PLATFORM, "Complete product"),
        (GROUP1_DEVICE, "Device, equipment or object"),
        (GROUP1_COMPONENTS, "Component, accessory or module"),
        (GROUP1_MATERIALS, "Material or substance"),
        (GROUP2_FIREARMS, "Firearm"),
        (GROUP3_SOFTWARE, "Software, information or technology"),
        (GROUP3_TECHNOLOGY, "Technology"),
    ]

    group_one = [GROUP1_PLATFORM, GROUP1_DEVICE, GROUP1_COMPONENTS, GROUP1_MATERIALS]
    group_two = [GROUP2_FIREARMS]
    group_three = [GROUP3_SOFTWARE, GROUP3_TECHNOLOGY]

    @classmethod
    def to_str(cls, obj):
        return next(choice[1] for choice in cls.choices if choice[0] == obj) if obj else None


class MilitaryUse:
    YES_DESIGNED = "yes_designed"
    YES_MODIFIED = "yes_modified"
    NO = "no"

    choices = [
        (YES_DESIGNED, "Yes, specially designed for military use"),
        (YES_MODIFIED, "Yes, modified for military use"),
        (NO, "No"),
    ]

    @classmethod
    def to_str(cls, obj):
        return next(choice[1] for choice in cls.choices if choice[0] == obj) if obj else None


class Component:
    YES_DESIGNED = "yes_designed"
    YES_MODIFIED = "yes_modified"
    YES_GENERAL_PURPOSE = "yes_general"
    NO = "no"

    choices = [
        (YES_DESIGNED, "Yes, it's designed specially for hardware"),
        (YES_MODIFIED, "Yes, it's been modified for hardware"),
        (YES_GENERAL_PURPOSE, "Yes, it's a general purpose component"),
        (NO, "No"),
    ]

    @classmethod
    def to_str(cls, obj):
        return next(choice[1] for choice in cls.choices if choice[0] == obj) if obj else None


class FirearmGoodType:
    FIREARMS = "firearms"
    COMPONENTS_FOR_FIREARMS = "components_for_firearms"
    AMMUNITION = "ammunition"
    COMPONENTS_FOR_AMMUNITION = "components_for_ammunition"
    FIREARMS_ACCESSORY = "firearms_accessory"
    SOFTWARE_RELATED_TO_FIREARM = "software_related_to_firearms"
    TECHNOLOGY_RELATED_TO_FIREARM = "technology_related_to_firearms"

    choices = [
        (FIREARMS, "Firearm"),
        (COMPONENTS_FOR_FIREARMS, "Components for firearms"),
        (AMMUNITION, "Ammunition"),
        (COMPONENTS_FOR_AMMUNITION, "Components for ammunition"),
        (FIREARMS_ACCESSORY, "Accessory of a firearm"),
        (SOFTWARE_RELATED_TO_FIREARM, "Software relating to a firearm"),
        (TECHNOLOGY_RELATED_TO_FIREARM, "Technology relating to a firearm"),
    ]

    @classmethod
    def to_str(cls, obj):
        return next(choice[1] for choice in cls.choices if choice[0] == obj) if obj else None


class FirearmCategory(models.TextChoices):
    NON_AUTOMATIC_SHOTGUN = "NON_AUTOMATIC_SHOTGUN", "Non automatic shotgun"
    NON_AUTOMATIC_RIM_FIRED_RIFLE = "NON_AUTOMATIC_RIM_FIRED_RIFLE", "Non automatic rim-fired rifle"
    NON_AUTOMATIC_RIM_FIRED_HANDGUN = "NON_AUTOMATIC_RIM_FIRED_HANDGUN", "Non automatic rim-fired handgun"
    RIFLE_MADE_BEFORE_1938 = "RIFLE_MADE_BEFORE_1938", "Rifle made before 1938"
    COMBINATION_GUN_MADE_BEFORE_1938 = "COMBINATION_GUN_MADE_BEFORE_1938", "Combination gun made before 1938"
    NONE = "NONE", "None of the above"
