from django.urls import reverse
from rest_framework import status
from test_helpers.clients import DataTestClient
from api.addresses.models import Address
from api.staticdata.countries.models import Country
from api.addresses.tests.factories import AddressFactory
from api.organisations.models import Site


class AddressDataWorkspaceTests(DataTestClient):
    def test_addresses(self):
        # Clear other records set up by DataTestClient
        Site.objects.all().delete()
        Address.objects.all().delete()
        # Create a new address record with specified values
        address = AddressFactory(
            address_line_1="some first line",
            address_line_2="some second line",
            region="Hampshire",
            postcode="SW1A 2PA",
            city="some city",
            country=Country.objects.get(pk="GB"),
        )
        url = reverse("data_workspace:dw-address-list")

        # Assert the full response is as expected
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "address_line_1": "some first line",
                        "address_line_2": "some second line",
                        "region": "Hampshire",
                        "postcode": "SW1A 2PA",
                        "city": "some city",
                        "country": {
                            "id": "GB",
                            "name": "Great Britain",
                            "type": "gov.uk Country",
                            "is_eu": False,
                            "report_name": "",
                        },
                        "id": str(address.id),
                    }
                ],
            },
        )
