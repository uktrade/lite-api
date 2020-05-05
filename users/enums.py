from uuid import UUID

from common.enums import LiteEnum, autostr
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


class UserType(LiteEnum):
    EXPORTER = autostr()
    INTERNAL = autostr()
    SYSTEM = autostr()

    @classmethod
    def non_system_choices(cls):
        return [(cls.EXPORTER, "Exporter"), (cls.INTERNAL, "Internal")]

    @classmethod
    def choices(cls):
        return cls.non_system_choices().append((cls.SYSTEM, "System"))

    def human_readable(self):
        return self.value.capitalize()


class SystemUser:
    id = UUID(SYSTEM_USER.get("id"))
    first_name = SYSTEM_USER.get("first_name")
    last_name = SYSTEM_USER.get("last_name")
