from django.urls import reverse
from rest_framework import status

from api.core.authentication import EXPORTER_USER_TOKEN_HEADER
from api.users.libraries.user_to_token import user_to_token
from test_helpers.clients import DataTestClient
from api.organisations.enums import OrganisationType
from lite_content.lite_api.strings import Addresses


class AddressSerializerPostcodeValidationTest(DataTestClient):
    url = reverse("organisations:organisations")

    def test_invalid_postcodes(self):
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
            response = self.client.post(
                self.url, data, **{EXPORTER_USER_TOKEN_HEADER: user_to_token(self.exporter_user.baseuser_ptr)}
            )

            self.assertEqual(response.json()["errors"]["site"]["address"]["postcode"][0], Addresses.POSTCODE)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_postcodes(self):
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

        valid_postcodes = [
            "BT32 4PX",
            "GIR 0AA",
            "BT324PX",
            " so11aa ",
            " so1  1aa ",
            "G2 3wt",
            "EC1A 1BB",
            "Ec1a1BB",
        ]

        for postcode in valid_postcodes:
            data["site"]["address"]["postcode"] = postcode
            response = self.client.post(
                self.url, data, **{EXPORTER_USER_TOKEN_HEADER: user_to_token(self.exporter_user.baseuser_ptr)}
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
