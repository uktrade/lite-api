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

    non_system_choices = [
        (EXPORTER, "Exporter"),
        (INTERNAL, "Internal"),
    ]

    choices = non_system_choices + [(SYSTEM, "System")]


class SystemUser:
    @property
    def id(self):
        return SYSTEM_USER.get("id")

    @property
    def first_name(self):
        return SYSTEM_USER.get("first_name")

    @property
    def last_name(self):
        return SYSTEM_USER.get("last_name")
