class UserStatuses:
    ACTIVE = "Active"
    DEACTIVATED = "Deactivated"

    choices = [
        (ACTIVE, "Active"),
        (DEACTIVATED, "Deactivated"),
    ]


class UserType:
    EXPORTER = "exporter"
    INTERNAL = "internal"

    choices = [
        (EXPORTER, "Exporter"),
        (INTERNAL, "Internal"),
    ]
