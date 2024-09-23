from rest_framework import status
from rest_framework.reverse import reverse

from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.control_list_entries.factories import ControlListEntriesFactory
from test_helpers.clients import DataTestClient


class ControlListEntriesListTests(DataTestClient):
    def setUp(self):
        self.url = reverse("caseworker_staticdata:control_list_entries:control_list_entries")
        super().setUp()
        ControlListEntry.objects.all().delete()
        self.parent_cle = ControlListEntriesFactory(
            rating="ML1",
            selectable_for_assessment=False,
            text="some ML1 text",
        )
        self.child_cle = ControlListEntriesFactory(
            rating="ML1a",
            parent=self.parent_cle,
            selectable_for_assessment=True,
            text="some ML1a text",
        )

    def test_GET_success(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            [
                {
                    "rating": "ML1a",
                    "text": "some ML1a text",
                    "parent": str(self.parent_cle.id),
                }
            ],
        )

    def test_GET_exporter_forbidden(self):
        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_GET_include_non_selectable_for_assessment_param(self):
        url = self.url + "?include_non_selectable_for_assessment=True"
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            [
                {
                    "rating": "ML1",
                    "text": "some ML1 text",
                    "parent": None,
                },
                {
                    "rating": "ML1a",
                    "text": "some ML1a text",
                    "parent": str(self.parent_cle.id),
                },
            ],
        )
