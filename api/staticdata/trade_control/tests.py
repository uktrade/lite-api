from rest_framework import status
from rest_framework.reverse import reverse

from api.static.trade_control.enums import TradeControlActivity, TradeControlProductCategory
from test_helpers.clients import DataTestClient


class ActivityTests(DataTestClient):
    def test_get_activities_success(self):
        url = reverse("static:trade_control:activities")

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["activities"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(TradeControlActivity.choices))
        for activity in TradeControlActivity.choices:
            self.assertIn(activity[0], str(response_data))


class ProductCategoryTests(DataTestClient):
    def test_get_product_categories_success(self):
        url = reverse("static:trade_control:product_categories")

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["product_categories"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(TradeControlProductCategory.choices))
        for product_category in TradeControlProductCategory.choices:
            self.assertIn(product_category[0], str(response_data))
