from enum import Enum


class TemplateType(Enum):
    APPLICATION_STATUS = "application_status"
    EXPORTER_REGISTERED_NEW_ORG = "exporter_registered_new_org"
    EXPORTER_USER_ADDED = "exporter_user_added"
    EXPORTER_LICENCE_ISSUED = "exporter_licence_issued"
    EXPORTER_ORGANISATION_APPROVED = "exporter_organisation_approved"
    EXPORTER_ORGANISATION_REJECTED = "exporter_organisation_rejected"
    CASEWORKER_REGISTERED_NEW_ORG = "caseworker_registered_new_org"
    EXPORTER_CASE_OPENED_FOR_EDITING = "exporter_editing"
    EXPORTER_ECJU_QUERY = "exporter_ecju_query"

    @property
    def template_id(self):
        """
        Return Gov Notify template ID for respective template type.
        """
        return {
            self.APPLICATION_STATUS: "b9c3403a-8d09-416e-acd3-99baabf5b043",
            self.EXPORTER_REGISTERED_NEW_ORG: "6096c45e-0cbb-4ecd-a7a9-0ad674e1d2c0",
            self.EXPORTER_USER_ADDED: "c9b67dca-0916-453a-99c0-70ba563e1bdd",
            self.EXPORTER_LICENCE_ISSUED: "f2757d61-2319-4279-82b2-a52170b0222a",
            self.EXPORTER_ORGANISATION_APPROVED: "d5e94717-ae78-4d18-8064-ecfcd99143f1",
            self.EXPORTER_ORGANISATION_REJECTED: "1dec3acd-94b0-47bb-832a-384ba5c6f51a",
            self.EXPORTER_ECJU_QUERY: "84431173-72a9-43a1-8926-b43dec7871f9",
            self.CASEWORKER_REGISTERED_NEW_ORG: "d835dba3-ca85-4a27-b257-e31a17f0e61d",
            self.EXPORTER_CASE_OPENED_FOR_EDITING: "73121bc2-2f03-4c66-8e88-61a156c05559",
        }[self]
