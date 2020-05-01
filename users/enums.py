from uuid import UUID

from conf.settings import SYSTEM_USER


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
    SYSTEM = "system"

    choices = [
        (EXPORTER, "Exporter"),
        (INTERNAL, "Internal"),
        (SYSTEM, "System"),
    ]


class SystemUser:
    ID = UUID(SYSTEM_USER.get("id"))
    FIRST_NAME = SYSTEM_USER.get("first_name")
    LAST_NAME = SYSTEM_USER.get("last_name")
