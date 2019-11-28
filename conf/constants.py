from enum import Enum
from uuid import UUID


class Permission(Enum):
    MANAGE_FINAL_ADVICE = "Manage final advice"
    MANAGE_TEAM_ADVICE = "Manage team advice"
    MANAGE_TEAM_CONFIRM_OWN_ADVICE = "Confirm own advice"
    REVIEW_GOODS = "Review goods"
    ADMINISTER_ROLES = "Administer roles"
    CONFIRM_OWN_ADVICE = "Confirm own advice"
    CONFIGURE_TEMPLATES = "Create and edit templates"


class Roles:
    DEFAULT_ROLE_ID = UUID("00000000-0000-0000-0000-000000000001")
    SUPER_USER_ROLE_ID = UUID("00000000-0000-0000-0000-000000000002")
