from django.urls import reverse
from rest_framework import status
from random import randint
from unittest import mock
from api.core.authentication import EXPORTER_USER_TOKEN_HEADER
from api.users.libraries.user_to_token import user_to_token
from test_helpers.clients import DataTestClient
from api.organisations.enums import OrganisationType
from lite_content.lite_api.strings import Addresses
from api.addresses.models import Address
from parameterized import parameterized


class AddressSerializerPostcodeValidationTest(DataTestClient):
    url = reverse("organisations:organisations")

    @mock.patch("api.core.celery_tasks.NotificationsAPIClient.send_email_notification")
    def test_invalid_postcodes(self, mock_gov_notification):
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
                },
            },
            "user": {"email": "trinity@bsg.com"},
        }

        invalid_postcodes = ["1NV 4L1D", "1NV4L1D", " b0gUS"]

        for postcode in invalid_postcodes:
            data["site"]["address"]["postcode"] = postcode
            data["registration_number"] = "".join([str(randint(0, 9)) for _ in range(8)])
            response = self.client.post(
                self.url, data, **{EXPORTER_USER_TOKEN_HEADER: user_to_token(self.exporter_user.baseuser_ptr)}
            )

            self.assertEqual(response.json()["errors"]["site"]["address"]["postcode"][0], Addresses.POSTCODE)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            ("BT32 4PX", "BT32 4PX"),
            ("GIR 0AA", "GIR 0AA"),
            ("BT324PX", "BT324PX"),
            (" so11aa ", "SO11AA"),
            (" so1  1aa ", "SO1  1AA"),
            ("G2 3wt", "G2 3WT"),
            ("EC1A 1BB", "EC1A 1BB"),
            ("Ec1a2Bb", "EC1A2BB"),
        ]
    )
    @mock.patch("api.core.celery_tasks.NotificationsAPIClient.send_email_notification")
    def test_valid_postcodes(self, valid_postcode, expected, mock_gov_notification):
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
                },
            },
            "user": {"email": "trinity@bsg.com"},
            "phone_number": "+441234567895",
            "website": "",
        }

        data["site"]["address"]["postcode"] = valid_postcode
        data["registration_number"] = "".join([str(randint(0, 9)) for _ in range(8)])
        response = self.client.post(
            self.url, data, **{EXPORTER_USER_TOKEN_HEADER: user_to_token(self.exporter_user.baseuser_ptr)}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        addr = Address.objects.get(postcode=expected)

        self.assertEqual(addr.postcode, expected)
