from enum import Enum


class TemplateType(Enum):
    ECJU_COMPLIANCE_CREATED = "ecju_compliance_created"
    APPLICATION_STATUS = "application_status"
    ORGANISATION_STATUS = "organisation_status"
    EXPORTER_REGISTERED_NEW_ORG = "exporter_registered_new_org"

    @property
    def template_id(self):
        """
        Return Gov Notify template ID for respective template type.
        """
        return {
            self.ECJU_COMPLIANCE_CREATED: "b23f4c55-fef0-4d8f-a10b-1ad7f8e7c672",
            self.APPLICATION_STATUS: "b9c3403a-8d09-416e-acd3-99baabf5b043",
            self.ORGANISATION_STATUS: "c57ef67e-14fd-4af9-a9b2-5015040fa408",
            self.EXPORTER_REGISTERED_NEW_ORG: "6096c45e-0cbb-4ecd-a7a9-0ad674e1d2c0",
        }[self]
