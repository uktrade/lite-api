from enum import Enum
from uuid import UUID


class GovPermissions(Enum):
    MANAGE_LICENCE_FINAL_ADVICE = "Manage licence final advice"
    MANAGE_CLEARANCE_FINAL_ADVICE = "Manage clearance final advice"
    MANAGE_TEAM_ADVICE = "Manage team advice"
    MANAGE_TEAM_CONFIRM_OWN_ADVICE = "Confirm own advice"
    REVIEW_GOODS = "Review goods"
    RESPOND_PV_GRADING = "Respond to grading"
    ADMINISTER_ROLES = "Administer roles"
    CONFIGURE_TEMPLATES = "Create and edit templates"
    REOPEN_CLOSED_CASES = "Can re-open closed cases"
    MANAGE_LICENCE_DURATION = "Can edit licence duration"
    MANAGE_ORGANISATIONS = "Manage organisations"
    MANAGE_FLAGGING_RULES = "Manage flagging rules"
    MANAGE_TEAM_ROUTING_RULES = "Manage team routing rules"
    MANAGE_ALL_ROUTING_RULES = "Manage all routing rules"
    ACTIVATE_FLAGS = "Activate and deactivate flags"
    MANAGE_PICKLISTS = "Manage picklists"


class ExporterPermissions(Enum):
    ADMINISTER_USERS = "Administer users"
    ADMINISTER_SITES = "Administer sites"
    EXPORTER_ADMINISTER_ROLES = "Administer roles"
    SUBMIT_LICENCE_APPLICATION = "Submit licence applications"
    SUBMIT_CLEARANCE_APPLICATION = "Submit clearance applications"


class Roles:
    INTERNAL_DEFAULT_ROLE_ID = UUID("00000000-0000-0000-0000-000000000001")
    INTERNAL_DEFAULT_ROLE_NAME = "Default"
    INTERNAL_SUPER_USER_ROLE_ID = UUID("00000000-0000-0000-0000-000000000002")
    INTERNAL_SUPER_USER_ROLE_NAME = "Super User"
    EXPORTER_SUPER_USER_ROLE_ID = UUID("00000000-0000-0000-0000-000000000003")
    EXPORTER_SUPER_USER_ROLE_NAME = "Super User"
    EXPORTER_DEFAULT_ROLE_ID = UUID("00000000-0000-0000-0000-000000000004")
    EXPORTER_DEFAULT_ROLE_NAME = "Default"

    IMMUTABLE_ROLES = [INTERNAL_SUPER_USER_ROLE_ID, EXPORTER_SUPER_USER_ROLE_ID, EXPORTER_DEFAULT_ROLE_ID]

    EXPORTER_PRESET_ROLES = [EXPORTER_SUPER_USER_ROLE_ID, EXPORTER_DEFAULT_ROLE_ID]


class Teams:
    ADMIN_TEAM_ID = "00000000-0000-0000-0000-000000000001"
    ADMIN_TEAM_NAME = "Admin"
