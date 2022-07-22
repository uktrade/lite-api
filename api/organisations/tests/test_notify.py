from unittest import mock

from django.conf import settings

from faker import Faker
from test_helpers.clients import DataTestClient

from api.organisations.tests.factories import OrganisationFactory
from api.users.tests.factories import UserOrganisationRelationshipFactory
from gov_notify.enums import TemplateType
from gov_notify.payloads import (
    ExporterRegistration,
    ExporterOrganisationApproved,
    ExporterOrganisationRejected,
    CaseWorkerNewRegistration,
)
from api.organisations import notify


class NotifyTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory()
        UserOrganisationRelationshipFactory(organisation=self.organisation, user=self.exporter_user)

    @mock.patch("api.organisations.notify.send_email")
    def test_notify_exporter_registration(self, mock_send_email):
        email = Faker().email()
        data = {"organisation_name": "testorgname"}
        expected_payload = ExporterRegistration(**data)

        notify.notify_exporter_registration(email, data)

        mock_send_email.assert_called_with(email, TemplateType.EXPORTER_REGISTERED_NEW_ORG, expected_payload)

    @mock.patch("api.organisations.notify.send_email")
    def test_exporter_organisation_approved(self, mock_send_email):
        expected_payload = ExporterOrganisationApproved(
            exporter_first_name=self.exporter_user.first_name,
            organisation_name=self.organisation.name,
            exporter_frontend_url="https://exporter.lite.service.localhost.uktrade.digital/",
        )

        notify.notify_exporter_organisation_approved(self.organisation)

        mock_send_email.assert_called_with(
            self.exporter_user.email, TemplateType.EXPORTER_ORGANISATION_APPROVED, expected_payload
        )

    @mock.patch("api.organisations.notify.send_email")
    def test_exporter_organisation_rejected(self, mock_send_email):
        expected_payload = ExporterOrganisationRejected(
            exporter_first_name=self.exporter_user.first_name,
            organisation_name=self.organisation.name,
        )

        notify.notify_exporter_organisation_rejected(self.organisation)

        mock_send_email.assert_called_with(
            self.exporter_user.email, TemplateType.EXPORTER_ORGANISATION_REJECTED, expected_payload
        )

    @mock.patch("api.organisations.notify.send_email")
    def test_notify_caseworker_new_registration(self, mock_send_email):
        email = Faker().email()
        settings.LITE_INTERNAL_NOTIFICATION_EMAILS = {"CASEWORKER_NEW_REGISTRATION": [email]}

        data = {"organisation_name": "testorgname", "applicant_email": Faker().email()}
        expected_payload = CaseWorkerNewRegistration(**data)

        notify.notify_caseworker_new_registration(data)
        mock_send_email.assert_called_with(email, TemplateType.CASEWORKER_REGISTERED_NEW_ORG, expected_payload)
