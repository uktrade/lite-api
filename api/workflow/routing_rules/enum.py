class RoutingRulesAdditionalFields:
    USERS = "users"
    CASE_TYPES = "case_types"
    FLAGS = "flags"
    COUNTRY = "country"

    choices = [
        (USERS, "Users"),
        (CASE_TYPES, "Case Types"),
        (FLAGS, "flags"),
        (COUNTRY, "Country"),
    ]


class StatusAction:
    DEACTIVATE = "deactivate"
    REACTIVATE = "reactivate"
