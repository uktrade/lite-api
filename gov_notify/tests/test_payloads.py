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
                payloads.EcjuComplianceCreatedEmailData,
                {
                    "query": "testquery",
                    "case_reference": "testref",
                    "site_name": "testsitename",
                    "site_address": "testaddress",
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
                payloads.OrganisationStatusEmailData,
                {
                    "organisation_name": "testorgname",
                },
            ),
        ]
    )
    def test_valid_input(self, dataclass, data):
        assert dataclass(**data).as_dict() == data
