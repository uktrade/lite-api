from unittest import mock

from api.organisations.enums import OrganisationStatus
from api.organisations.helpers import notify_organisation_reviewed
from api.organisations.tests.factories import OrganisationFactory
from test_helpers.clients import DataTestClient


class TestHelpers(DataTestClient):
    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory(status=OrganisationStatus.IN_REVIEW)

    @mock.patch("api.organisations.notify.notify_exporter_organisation_approved")
    def test_notify_organisation_reviewed_active(self, mocked_notify):
        decision = OrganisationStatus.ACTIVE
        notify_organisation_reviewed(self.organisation, decision)
        mocked_notify.assert_called_with(self.organisation)

    @mock.patch("api.organisations.notify.notify_exporter_organisation_rejected")
    def test_notify_organisation_reviewed_rejected(self, mocked_notify):
        decision = OrganisationStatus.REJECTED
        notify_organisation_reviewed(self.organisation, decision)
        mocked_notify.assert_called_with(self.organisation)
