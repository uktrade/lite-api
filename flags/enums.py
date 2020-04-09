class FlagLevels:
    CASE = "Case"
    ORGANISATION = "Organisation"
    GOOD = "Good"
    DESTINATION = "Destination"

    choices = [
        (CASE, "Case"),
        (ORGANISATION, "Organisation"),
        (GOOD, "Good"),
        (DESTINATION, "Destination"),
    ]


class FlagStatuses:
    ACTIVE = "Active"
    DEACTIVATED = "Deactivated"

    choices = [
        (ACTIVE, "Active"),
        (DEACTIVATED, "Deactivated"),
    ]


class FlagColours:
    DEFAULT = "default"
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"
    ORANGE = "orange"
    BROWN = "brown"
    TURQUOISE = "turquoise"
    PINK = "pink"

    choices = [
        (DEFAULT, "Default"),
        (RED, "Red"),
        (YELLOW, "Yellow"),
        (GREEN, "Green"),
        (BLUE, "Blue"),
        (PURPLE, "Purple"),
        (ORANGE, "Orange"),
        (BROWN, "Brown"),
        (TURQUOISE, "Turquoise"),
        (PINK, "Pink"),
    ]


class SystemFlags:
    REFUSAL_FLAG_ID = "00000000-0000-0000-0000-000000000001"
    GOOD_CLC_QUERY_ID = "00000000-0000-0000-0000-000000000002"
    GOOD_PV_GRADING_QUERY_ID = "00000000-0000-0000-0000-000000000003"
    GOOD_NOT_YET_VERIFIED_ID = "00000000-0000-0000-0000-000000000004"
    MILITARY_END_USE_ID = "00000000-0000-0000-0000-000000000005"
    WMD_END_USE_ID = "00000000-0000-0000-0000-000000000006"
    FIREARMS_ID = "00000000-0000-0000-0000-000000000007"
    MARITIME_ANTI_PIRACY_ID = "00000000-0000-0000-0000-000000000008"

    list = [
        REFUSAL_FLAG_ID,
        GOOD_CLC_QUERY_ID,
        GOOD_PV_GRADING_QUERY_ID,
        GOOD_NOT_YET_VERIFIED_ID,
        MILITARY_END_USE_ID,
        WMD_END_USE_ID,
        FIREARMS_ID,
        MARITIME_ANTI_PIRACY_ID,
    ]
