from django.urls import reverse
from unittest.mock import patch

from test_helpers.clients import DataTestClient


class ProductSearchTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.product_search_url = reverse("product_search-list")

    @patch("api.search.product.views.ProductDocumentView", spec=True)
    def test_query_string_query_backend_search_fields_as_list(self, mock_view):
        """
        Search fields are specified as dict but that is not provided then the
        backend falls back to 'search_fields' list. In this test we delete the dict
        to test whether it falls back to using the list.
        We are always going to use dict but to address test coverage we need to check
        with list as well.
        """
        delattr(mock_view.__class__, "query_string_search_fields")

        response = self.client.get(self.product_search_url, {"search": "shifter AND 6A004"}, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

    @patch("api.search.product.views.ProductDocumentView", spec=True)
    def test_query_string_query_backend_search_fields_with_boost(self, mock_view):
        query_fields_with_boost = {
            "name": {"boost": 2},
            "part_number": None,
            "report_summary": None,
            "organisation": None,
        }
        setattr(mock_view.__class__, "query_string_search_fields", query_fields_with_boost)

        response = self.client.get(self.product_search_url, {"search": "shifter AND 6A004"}, **self.gov_headers)
        self.assertEqual(response.status_code, 200)
