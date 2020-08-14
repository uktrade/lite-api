from uuid import UUID

from api.common.enums import LiteEnum, autostr


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


class UserType(LiteEnum):
    EXPORTER = autostr()
    INTERNAL = autostr()
    SYSTEM = autostr()

    @classmethod
    def non_system_choices(cls):
        return [(cls.EXPORTER, "Exporter"), (cls.INTERNAL, "Internal")]

    @classmethod
    def choices(cls):
        return cls.non_system_choices() + [(cls.SYSTEM, "System")]

    def human_readable(self):
        return self.value.capitalize()


class SystemUser:
    id = UUID("00000000-0000-0000-0000-000000000001")
    first_name = "LITE"
    last_name = "system"
