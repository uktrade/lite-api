from enum import Enum
from uuid import UUID


class GovPermissions(Enum):
    MANAGE_FINAL_ADVICE = "Manage final advice"
    MANAGE_TEAM_ADVICE = "Manage team advice"
    MANAGE_TEAM_CONFIRM_OWN_ADVICE = "Confirm own advice"
    REVIEW_GOODS = "Review goods"
    ADMINISTER_ROLES = "Administer roles"
    CONFIRM_OWN_ADVICE = "Confirm own advice"
    CONFIGURE_TEMPLATES = "Create and edit templates"


class ExporterPermissions(Enum):
    ADMINISTER_USERS = "Administer users"
    ADMINISTER_SITES = "Administer sites"
    EXPORTER_ADMINISTER_ROLES = "Administer roles"
    SUBMIT_LICENCE_APPLICATION = "Submit licence applications"
    SUBMIT_CLEARANCE_APPLICATION = "Submit clearance applications"


class Roles:
    INTERNAL_DEFAULT_ROLE_ID = UUID("00000000-0000-0000-0000-000000000001")
    INTERNAL_SUPER_USER_ROLE_ID = UUID("00000000-0000-0000-0000-000000000002")
    EXPORTER_SUPER_USER_ROLE_ID = UUID("00000000-0000-0000-0000-000000000003")
    EXPORTER_DEFAULT_ROLE_ID = UUID("00000000-0000-0000-0000-000000000004")

    IMMUTABLE_ROLES = [INTERNAL_SUPER_USER_ROLE_ID, EXPORTER_SUPER_USER_ROLE_ID, EXPORTER_DEFAULT_ROLE_ID]

    EXPORTER_PRESET_ROLES = [EXPORTER_SUPER_USER_ROLE_ID, EXPORTER_DEFAULT_ROLE_ID]


skip_av_for_end_to_end_testing = False
