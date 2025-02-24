from django.urls import reverse
from rest_framework import status
from random import randint
from unittest import mock
from api.core.authentication import EXPORTER_USER_TOKEN_HEADER
from api.users.libraries.user_to_token import user_to_token
from test_helpers.clients import DataTestClient
from api.organisations.enums import OrganisationType
from lite_content.lite_api.strings import Addresses


class AddressSerializerPostcodeValidationTest(DataTestClient):
    url = reverse("organisations:organisations")

    @mock.patch("api.core.celery_tasks.NotificationsAPIClient.send_email_notification")
    def test_required_address_fields(self, mock_gov_notification):
        data = {
            "name": "Lemonworld Co",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": "01110",
            "vat_number": "GB123456789",
            "registration_number": "98765432",
            "site": {
                "name": "Headquarters",
                "address": {
                    "address_line_1": "42 Industrial Estate",
                    "address_line_2": "w3r",
                    "region": "",
                    "city": "St Albans",
                    "postcode": "BT32 4PX",
                },
            },
            "user": {"email": "trinity@bsg.com"},
            "phone_number": "+441234567895",
            "website": "",
        }

        data["registration_number"] = "".join([str(randint(0, 9)) for _ in range(8)])
        response = self.client.post(
            self.url, data, **{EXPORTER_USER_TOKEN_HEADER: user_to_token(self.exporter_user.baseuser_ptr)}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @mock.patch("api.core.celery_tasks.NotificationsAPIClient.send_email_notification")
    def test_valid(self, mock_gov_notification):
        data = {
            "name": "Lemonworld Co",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": "01110",
            "vat_number": "GB123456789",
            "registration_number": "98765432",
            "site": {
                "name": "Headquarters",
                "address": {
                    "address_line_1": "42 Industrial Estate",
                    "address_line_2": "Queens Road",
                    "region": "Hertfordshire",
                    "city": "St Albans",
                    "postcode": "BT32 4PX",
                },
            },
            "user": {"email": "trinity@bsg.com"},
            "phone_number": "+441234567895",
            "website": "",
        }

        data["registration_number"] = "".join([str(randint(0, 9)) for _ in range(8)])
        response = self.client.post(
            self.url, data, **{EXPORTER_USER_TOKEN_HEADER: user_to_token(self.exporter_user.baseuser_ptr)}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @mock.patch("api.core.celery_tasks.NotificationsAPIClient.send_email_notification")
    def test_empty_address_fields(self, mock_gov_notification):
        data = {
            "name": "Lemonworld Co",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": "01110",
            "vat_number": "GB123456789",
            "registration_number": "98765432",
            "site": {
                "name": "Headquarters",
                "address": {
                    "address_line_1": "",
                    "address_line_2": "",
                    "region": "",
                    "city": "",
                    "postcode": "",
                },
            },
            "user": {"email": "trinity@bsg.com"},
            "phone_number": "+441234567895",
            "website": "",
        }

        data["registration_number"] = "".join([str(randint(0, 9)) for _ in range(8)])
        response = self.client.post(
            self.url, data, **{EXPORTER_USER_TOKEN_HEADER: user_to_token(self.exporter_user.baseuser_ptr)}
        )
        address = response.json()["errors"]["site"]["address"]

        self.assertEqual(address["postcode"][0], Addresses.POSTCODE)
        self.assertEqual(address["address_line_1"][0], Addresses.ADDRESS_LINE_1)
        self.assertEqual(address["city"][0], Addresses.CITY)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
