class UserStatuses:
    ACTIVE = "Active"
    DEACTIVATED = "Deactivated"

    choices = [
        (ACTIVE, "Active"),
        (DEACTIVATED, "Deactivated"),
    ]

    @classmethod
    def from_string(cls, s):
        return {
            UserStatuses.ACTIVE.lower(): UserStatuses.ACTIVE,
            UserStatuses.DEACTIVATED.lower(): UserStatuses.DEACTIVATED,
        }[s.lower()]


class UserType:
    EXPORTER = "exporter"
    INTERNAL = "internal"

    choices = [
        (EXPORTER, "Exporter"),
        (INTERNAL, "Internal"),
    ]
