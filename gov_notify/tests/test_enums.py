from unittest import mock

from parameterized import parameterized
from rest_framework.test import APITestCase

from gov_notify.enums import TemplateType


class TemplateTypeTests(APITestCase):
    @parameterized.expand(
        [
            (TemplateType.APPLICATION_STATUS, "b9c3403a-8d09-416e-acd3-99baabf5b043"),
            (TemplateType.EXPORTER_REGISTERED_NEW_ORG, "6096c45e-0cbb-4ecd-a7a9-0ad674e1d2c0"),
            (TemplateType.EXPORTER_USER_ADDED, "c9b67dca-0916-453a-99c0-70ba563e1bdd"),
            (TemplateType.EXPORTER_ORGANISATION_APPROVED, "d5e94717-ae78-4d18-8064-ecfcd99143f1"),
            (TemplateType.EXPORTER_ORGANISATION_REJECTED, "1dec3acd-94b0-47bb-832a-384ba5c6f51a"),
        ]
    )
    def test_template_id(self, template_type, expected_template_id):
        assert template_type.template_id == expected_template_id
