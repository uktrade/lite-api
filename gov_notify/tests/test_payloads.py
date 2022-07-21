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
        ]
    )
    def test_valid_input(self, dataclass, data):
        assert dataclass(**data).as_dict() == data
