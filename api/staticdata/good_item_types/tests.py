from rest_framework import status
from rest_framework.reverse import reverse

from api.goods.enums import ItemType
from test_helpers.clients import DataTestClient
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class ItemTypeTests(DataTestClient):

    url = reverse("staticdata:item-types:item_types")

    def test_get_good_item_types(self):
        response = self.client.get(self.url, **self.exporter_headers)
        types = response.json()["item_types"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(types["equipment"], "Equipment")
        self.assertEqual(len(types), len(ItemType.choices))


class GoodItemTypesResponseTests(EndPointTests):
    url = "/staticdata/item-types/"

    def test_item_types(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)
