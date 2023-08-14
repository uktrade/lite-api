from unittest import mock

from parameterized import parameterized
from rest_framework.test import APITestCase

from gov_notify import payloads


class DataclassTests(APITestCase):
    @parameterized.expand(
        [
            (
                payloads.EcjuCreatedEmailData,
                {
                    "case_reference": "testref",
                    "application_reference": "testref2",
                    "link": "testlink",
                },
            ),
            (
                payloads.ApplicationStatusEmailData,
                {
                    "case_reference": "testref",
                    "application_reference": "testref2",
                    "link": "testlink",
                },
            ),
            (
                payloads.ExporterRegistration,
                {
                    "organisation_name": "testorgname",
                },
            ),
            (
                payloads.ExporterUserAdded,
                {
                    "organisation_name": "testorgname",
                    "exporter_frontend_url": "https://some.domain/foo",
                },
            ),
            (
                payloads.ExporterOrganisationApproved,
                {
                    "exporter_first_name": "testname",
                    "organisation_name": "testorgname",
                    "exporter_frontend_url": "https://some.domain/foo",
                },
            ),
            (
                payloads.ExporterOrganisationRejected,
                {
                    "exporter_first_name": "testname",
                    "organisation_name": "testorgname",
                },
            ),
            (
                payloads.ExporterECJUQuery,
                {
                    "case_reference": "testref",
                    "exporter_first_name": "testname",
                    "exporter_frontend_url": "https://some.domain/foo",
                },
            ),
            (
                payloads.ExporterECJUQuery,
                {
                    "case_reference": "testref",
                    "exporter_first_name": "testname",
                    "exporter_frontend_url": "https://some.domain/foo",
                },
            ),
            (
                payloads.ExporterCaseOpenedForEditing,
                {
                    "application_reference": "testref",
                    "user_first_name": "testname",
                    "exporter_frontend_url": "https://some.domain/foo",
                },
            ),
            (
                payloads.ExporterNoLicenceRequired,
                {
                    "application_reference": "testref",
                    "user_first_name": "testname",
                    "exporter_frontend_url": "https://some.domain/foo",
                },
            ),
            (
                payloads.ExporterInformLetter,
                {
                    "application_reference": "testref",
                    "user_first_name": "testname",
                    "exporter_frontend_url": "https://some.domain/foo",
                },
            ),
            (
                payloads.CaseWorkerNewRegistration,
                {
                    "organisation_name": "testref",
                    "applicant_email": "test@user.com",
                },
            ),
        ]
    )
    def test_valid_input(self, dataclass, data):
        assert dataclass(**data).as_dict() == data
