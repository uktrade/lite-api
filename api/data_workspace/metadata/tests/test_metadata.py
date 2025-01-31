from django.urls import (
    include,
    path,
    reverse,
)

from rest_framework.test import URLPatternsTestCase


class MetadataTestCase(URLPatternsTestCase):
    databases = {"default"}
    urlpatterns = [
        path("api/", include("api.data_workspace.metadata.tests.urls")),
        path("namespaced/", include(("api.data_workspace.metadata.tests.urls", "namespaced"), namespace="namespaced")),
        path(
            "auto-fields/",
            include(("api.data_workspace.metadata.tests.auto_field_urls", "auto-fields"), namespace="auto-fields"),
        ),
    ]

    def setUp(self):
        super().setUp()

        self.url = reverse("table-metadata")
        self.namespaced_url = reverse("namespaced:table-metadata")
        self.auto_fields_url = reverse("auto-fields:table-metadata")

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

    def assertFieldsEqual(self, output, table_name, fields):
        for table in output["tables"]:
            if table["table_name"] == table_name:
                self.assertEqual(
                    table["fields"],
                    fields,
                )
                break
        else:
            self.fail(f"No table found with name {table_name}")

    def test_hidden_field_definition(self):
        response = self.client.get(self.auto_fields_url)
        output = response.json()
        self.assertFieldsEqual(
            output,
            "hidden_field",
            [],
        )

    def test_uuid_field_definition(self):
        response = self.client.get(self.auto_fields_url)
        output = response.json()
        self.assertFieldsEqual(
            output,
            "uuid_field",
            [
                {"name": "uuid_field", "type": "UUID"},
                {"name": "nullable_uuid_field", "type": "UUID", "nullable": True},
            ],
        )

    def test_char_field_definition(self):
        response = self.client.get(self.auto_fields_url)
        output = response.json()
        self.assertFieldsEqual(
            output,
            "char_field",
            [
                {"name": "char_field", "type": "String"},
                {"name": "nullable_char_field", "type": "String", "nullable": True},
            ],
        )

    def test_serializer_method_field(self):
        response = self.client.get(self.auto_fields_url)
        output = response.json()
        self.assertFieldsEqual(
            output,
            "serializer_method_field",
            [
                {"name": "returns_string", "type": "String"},
                {"name": "returns_optional_string", "type": "String", "nullable": True},
                {"name": "returns_datetime", "type": "DateTime"},
                {"name": "returns_optional_datetime", "type": "DateTime", "nullable": True},
            ],
        )

    def test_float_field(self):
        response = self.client.get(self.auto_fields_url)
        output = response.json()
        self.assertFieldsEqual(
            output,
            "float_field",
            [
                {"name": "float_field", "type": "Float"},
                {"name": "nullable_float_field", "type": "Float", "nullable": True},
            ],
        )

    def test_decimal_field(self):
        response = self.client.get(self.auto_fields_url)
        output = response.json()
        self.assertFieldsEqual(
            output,
            "decimal_field",
            [
                {"name": "decimal_field", "type": "Float", "asdecimal": True},
                {"name": "nullable_decimal_field", "type": "Float", "asdecimal": True, "nullable": True},
            ],
        )

    def test_integer_field(self):
        response = self.client.get(self.auto_fields_url)
        output = response.json()
        self.assertFieldsEqual(
            output,
            "integer_field",
            [
                {"name": "integer_field", "type": "Integer"},
                {"name": "nullable_integer_field", "type": "Integer", "nullable": True},
            ],
        )

    def test_auto_primary_key(self):
        response = self.client.get(self.auto_fields_url)
        output = response.json()
        self.assertFieldsEqual(
            output,
            "auto_primary_key",
            [
                {"name": "id", "type": "UUID", "primary_key": True},
                {"name": "not_a_primary_key", "type": "UUID"},
            ],
        )

    def test_explicit_primary_key(self):
        response = self.client.get(self.auto_fields_url)
        output = response.json()
        self.assertFieldsEqual(
            output,
            "explicit_primary_key",
            [
                {"name": "a_different_id", "type": "UUID", "primary_key": True},
                {"name": "not_a_primary_key", "type": "UUID"},
            ],
        )
