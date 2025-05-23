from enum import Enum


class TemplateType(Enum):
    APPLICATION_STATUS = "application_status"
    EXPORTER_REGISTERED_NEW_ORG = "exporter_registered_new_org"
    EXPORTER_USER_ADDED = "exporter_user_added"
    EXPORTER_LICENCE_ISSUED = "exporter_licence_issued"
    EXPORTER_LICENCE_REFUSED = "exporter_licence_refused"
    EXPORTER_LICENCE_REVOKED = "exporter_licence_revoked"
    EXPORTER_LICENCE_SUSPENDED = "exporter_licence_suspended"
    EXPORTER_ORGANISATION_APPROVED = "exporter_organisation_approved"
    EXPORTER_ORGANISATION_REJECTED = "exporter_organisation_rejected"
    EXPORTER_CASE_OPENED_FOR_EDITING = "exporter_editing"
    EXPORTER_ECJU_QUERY = "exporter_ecju_query"
    EXPORTER_ECJU_QUERY_CHASER = "exporter_ecju_query_chaser"
    EXPORTER_F680_ECJU_QUERY = "exporter_f680_ecju_query"
    EXPORTER_F680_ECJU_QUERY_CHASER = "exporter_f680_ecju_query_chaser"
    EXPORTER_F680_OUTCOME_ISSUED = "exporter_f680_outcome_issued"
    EXPORTER_NO_LICENCE_REQUIRED = "exporter_no_licence_required"
    EXPORTER_INFORM_LETTER = "exporter_inform_letter"
    EXPORTER_APPEAL_ACKNOWLEDGEMENT = "exporter_appeal_acknowledgement"
    CASEWORKER_REGISTERED_NEW_ORG = "caseworker_registered_new_org"
    CASEWORKER_COUNTERSIGN_CASE_RETURN = "caseworker_countersign_case_return"

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
            self.EXPORTER_LICENCE_REFUSED: "6d8089be-9551-456d-8305-d4185555f725",
            self.EXPORTER_LICENCE_REVOKED: "05cec19b-2e65-480d-b859-7116aa5c2e44",
            self.EXPORTER_LICENCE_SUSPENDED: "4ce5133f-38c1-48c4-b31f-cb0dbb4bb59e",
            self.EXPORTER_ORGANISATION_APPROVED: "d5e94717-ae78-4d18-8064-ecfcd99143f1",
            self.EXPORTER_ORGANISATION_REJECTED: "1dec3acd-94b0-47bb-832a-384ba5c6f51a",
            self.EXPORTER_ECJU_QUERY: "84431173-72a9-43a1-8926-b43dec7871f9",
            self.EXPORTER_ECJU_QUERY_CHASER: "3ba8579c-ba2a-40bc-a302-9429cc465c96",
            self.EXPORTER_F680_ECJU_QUERY: "aaa28b9e-9e12-4649-8c7d-036acaba8f14",
            self.EXPORTER_F680_ECJU_QUERY_CHASER: "e887f093-acb8-4fcb-97ca-e24aa747880f",
            self.EXPORTER_F680_OUTCOME_ISSUED: "dc73cc00-d38f-4ef8-b193-226b37fde612",
            self.EXPORTER_CASE_OPENED_FOR_EDITING: "73121bc2-2f03-4c66-8e88-61a156c05559",
            self.EXPORTER_NO_LICENCE_REQUIRED: "d84d1843-882c-440e-9cd4-84972ba612e6",
            self.EXPORTER_INFORM_LETTER: "7b63296f-af08-46bf-961e-19bdde93761c",
            self.EXPORTER_APPEAL_ACKNOWLEDGEMENT: "4fea1cd2-c386-4390-a9ab-fc7c2b0dade7",
            self.CASEWORKER_REGISTERED_NEW_ORG: "d835dba3-ca85-4a27-b257-e31a17f0e61d",
            self.CASEWORKER_COUNTERSIGN_CASE_RETURN: "4d418015-cd7c-498f-a972-72e7ec4468cc",
        }[self]
