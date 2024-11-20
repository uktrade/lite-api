from django.urls import (
    include,
    path,
    reverse,
)

from rest_framework.test import URLPatternsTestCase


class MetadataTestCase(URLPatternsTestCase):
    urlpatterns = [
        path("api/", include("api.data_workspace.metadata.tests.urls")),
    ]

    def setUp(self):
        super().setUp()

        self.url = reverse("table-metadata")

    def test_metadata_endpoint(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_metadata_tables_definitions(self):
        response = self.client.get(self.url)
        output = response.json()
        self.assertEqual(
            output["tables"],
            [
                {
                    "table_name": "fake_table",
                    "endpoint": "http://testserver/api/endpoints/fake-table/",
                },
            ],
        )
