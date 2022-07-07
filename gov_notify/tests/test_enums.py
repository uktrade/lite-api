from unittest import mock

from parameterized import parameterized
from rest_framework.test import APITestCase

from gov_notify.enums import TemplateType


class TemplateTypeTests(APITestCase):
    @parameterized.expand(
        [
            (TemplateType.ECJU_CREATED, "bcf052e0-54d9-4ed2-b77e-2f5a77589466"),
            (TemplateType.ECJU_COMPLIANCE_CREATED, "b23f4c55-fef0-4d8f-a10b-1ad7f8e7c672"),
            (TemplateType.APPLICATION_STATUS, "b9c3403a-8d09-416e-acd3-99baabf5b043"),
            (TemplateType.ORGANISATION_STATUS, "c57ef67e-14fd-4af9-a9b2-5015040fa408"),
            (TemplateType.EXPORTER_REGISTERED_NEW_ORG, "6096c45e-0cbb-4ecd-a7a9-0ad674e1d2c0"),
        ]
    )
    def test_template_id(self, template_type, expected_template_id):
        assert template_type.template_id == expected_template_id
