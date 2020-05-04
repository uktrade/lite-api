from uuid import UUID

from common.enums import LiteEnum, autostr


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

    @classmethod
    def choices(cls):
        return [(cls.EXPORTER, "Exporter"), (cls.INTERNAL, "Internal")]

    def human_readable(self):
        return self.value.capitalize()


class SystemUser:
    LITE_SYSTEM_ID = UUID("00000000-0000-0000-0000-000000000000")
