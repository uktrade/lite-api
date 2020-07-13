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
    YES = "yes"
    NO = "no"
    UNSURE = "unsure"

    choices = [(YES, "Yes"), (NO, "No"), (UNSURE, "I don't know")]


class GoodPvGraded:
    YES = "yes"
    NO = "no"
    GRADING_REQUIRED = "grading_required"

    choices = [(YES, "Yes"), (NO, "No"), (GRADING_REQUIRED, "Good needs to be graded")]


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

    gov_choices = [
        (UK_UNCLASSIFIED, "UK unclassified"),
        (UK_OFFICIAL, "UK official"),
        (UK_OFFICIAL_SENSITIVE, "UK official - sensitive"),
        (UK_SECRET, "UK secret"),
        (UK_TOP_SECRET, "UK top secret"),
    ]

    @classmethod
    def to_str(cls, obj):
        return next(grading[1] for grading in cls.choices if grading[0] == obj)


class ItemCategory:
    GROUP1_PLATFORM = "group1_platform"
    GROUP1_DEVICE = "group1_device"
    GROUP1_COMPONENTS = "group1_components"
    GROUP1_MATERIALS = "group1_materials"
    GROUP2_FIREARMS = "group2_firearms"
    GROUP3_SOFTWARE = "group3_software"
    GROUP3_TECHNOLOGY = "group3_technology"

    choices = [
        (GROUP1_PLATFORM, "Platform, vehicle, system or machine"),
        (GROUP1_DEVICE, "Device, equipment or object"),
        (GROUP1_COMPONENTS, "Components, modules or accessories of something"),
        (GROUP1_MATERIALS, "Materials or substances"),
        (GROUP2_FIREARMS, "Firearms"),
        (GROUP3_SOFTWARE, "Software"),
        (GROUP3_TECHNOLOGY, "Technology"),
    ]

    group_one = [GROUP1_PLATFORM, GROUP1_DEVICE, GROUP1_COMPONENTS, GROUP1_MATERIALS]
    group_two = [GROUP2_FIREARMS]
    group_three = [GROUP3_SOFTWARE, GROUP3_TECHNOLOGY]

    @classmethod
    def to_str(cls, obj):
        return next(grading[1] for grading in cls.choices if grading[0] == obj)


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
        return next(grading[1] for grading in cls.choices if grading[0] == obj)


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
        return next(grading[1] for grading in cls.choices if grading[0] == obj)


class FirearmGoodType:
    FIREARMS = "firearms"
    COMPONENTS_FOR_FIREARMS = "components_for_firearms"
    AMMUNITION = "ammunition"
    COMPONENTS_FOR_AMMUNITION = "components_for_ammunition"

    choices = [
        (FIREARMS, "Firearms"),
        (COMPONENTS_FOR_FIREARMS, "Components for firearms"),
        (AMMUNITION, "Ammunition"),
        (COMPONENTS_FOR_AMMUNITION, "Components for ammunition"),
    ]

    @classmethod
    def to_str(cls, obj):
        return next(grading[1] for grading in cls.choices if grading[0] == obj)
