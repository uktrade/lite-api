from django.urls import (
    include,
    path,
    reverse,
)

from rest_framework.test import URLPatternsTestCase


class MetadataTestCase(URLPatternsTestCase):
    urlpatterns = [
        path("api/", include("api.data_workspace.metadata.tests.urls")),
        path("namespaced/", include(("api.data_workspace.metadata.tests.urls", "namespaced"), namespace="namespaced")),
    ]

    def setUp(self):
        super().setUp()

        self.url = reverse("table-metadata")
        self.namespaced_url = reverse("namespaced:table-metadata")

    def test_metadata_endpoint(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_urls(self):
        self.assertEqual(
            reverse("dw-fake-table-list"),
            "/api/endpoints/fake-table/",
        )
        self.assertEqual(
            reverse("dw-fake-table-detail", kwargs={"pk": "test"}),
            "/api/endpoints/fake-table/test/",
        )

        self.assertEqual(
            reverse("namespaced:dw-fake-table-list"),
            "/namespaced/endpoints/fake-table/",
        )
        self.assertEqual(
            reverse("namespaced:dw-fake-table-detail", kwargs={"pk": "test"}),
            "/namespaced/endpoints/fake-table/test/",
        )

    def test_metadata_tables_definitions(self):
        response = self.client.get(self.url)
        output = response.json()
        self.assertEqual(
            output["tables"],
            [
                {
                    "table_name": "fake_table",
                    "endpoint": "http://testserver/api/endpoints/fake-table/",
                    "indexes": [],
                    "fields": [],
                },
                {
                    "table_name": "another_fake_table",
                    "endpoint": "http://testserver/api/endpoints/another-fake-table/",
                    "indexes": ["one", "two", "three"],
                    "fields": [{"name": "id", "primary_key": True, "type": "UUID"}],
                },
            ],
        )

    def test_metadata_tables_definitions_with_namespace(self):
        response = self.client.get(self.namespaced_url)
        output = response.json()
        self.assertEqual(
            output["tables"],
            [
                {
                    "table_name": "fake_table",
                    "endpoint": "http://testserver/namespaced/endpoints/fake-table/",
                    "indexes": [],
                    "fields": [],
                },
                {
                    "table_name": "another_fake_table",
                    "endpoint": "http://testserver/namespaced/endpoints/another-fake-table/",
                    "indexes": ["one", "two", "three"],
                    "fields": [{"name": "id", "primary_key": True, "type": "UUID"}],
                },
            ],
        )
