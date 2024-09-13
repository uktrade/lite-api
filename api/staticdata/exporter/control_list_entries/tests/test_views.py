from rest_framework import status
from rest_framework.reverse import reverse

from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.control_list_entries.factories import ControlListEntriesFactory
from test_helpers.clients import DataTestClient


class ControlListEntriesListTests(DataTestClient):
    def setUp(self):
        self.url = reverse("exporter_staticdata:control_list_entries:control_list_entries")
        super().setUp()

    def test_list_view_success(self):
        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(len(response.json()) > 0)

        for cle in response.json():
            self.assertEqual(list(cle.keys()), ["rating", "text"])

    def test_list_view_failure_bad_headers(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_view_success_exact_response(self):
        # Set up empty CLE db table for this test only
        ControlListEntry.objects.all().delete()

        cle_1 = ControlListEntriesFactory(rating="ABC123", controlled=True)
        cle_2 = ControlListEntriesFactory(rating="1Z101", controlled=True)
        cle_3 = ControlListEntriesFactory(rating="ZXYW", controlled=True)

        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            [
                {"rating": cle_1.rating, "text": cle_1.text},
                {"rating": cle_2.rating, "text": cle_2.text},
                {"rating": cle_3.rating, "text": cle_3.text},
            ],
        )

    def test_list_view_ignores_unselectable_cles_by_default(self):
        cles_count_model = ControlListEntry.objects.all().count()

        # Assert that we have at least 1 CLE returned by the db manager
        self.assertTrue(cles_count_model > 0)

        response = self.client.get(self.url, **self.exporter_headers)
        cles_data = response.json()
        cles_count_data = len(cles_data)

        # Assert that we have at least 1 CLE returned by the view
        self.assertTrue(cles_count_data > 0)

        # Create a CLE with selectable_for_assessment=False
        unselectable_cle = ControlListEntriesFactory(rating="rating123", text="text", selectable_for_assessment=False)

        # Assert that the object was created successfully
        self.assertFalse(unselectable_cle.selectable_for_assessment)
        self.assertTrue(
            ControlListEntry.objects.filter(rating="rating123", selectable_for_assessment=False).count() == 1
        )

        updated_cles_count_model = ControlListEntry.objects.all().count()

        # Assert that the count returned by the db manager has increased by 1
        self.assertTrue(updated_cles_count_model == cles_count_model + 1)

        response = self.client.get(self.url, **self.exporter_headers)
        updated_cles_data = response.json()
        updated_cles_count_data = len(updated_cles_data)

        # Assert that the count returned by the view is unchanged
        self.assertTrue(updated_cles_count_data == cles_count_data)

        # Assert that the data returned by the view does not contain the unselectable CLE
        self.assertNotIn("rating123", [cle["rating"] for cle in updated_cles_data])

    def test_list_view_includes_unselectable_cles_if_include_unselectable_is_true(self):
        url = reverse("exporter_staticdata:control_list_entries:control_list_entries") + "?include_unselectable=True"
        cles_count_model = ControlListEntry.objects.all().count()

        # Assert that we have at least 1 CLE returned by the db manager
        self.assertTrue(cles_count_model > 0)

        response = self.client.get(url, **self.exporter_headers)
        cles_data = response.json()
        cles_count_data = len(cles_data)

        # Assert that we have at least 1 CLE returned by the view
        self.assertTrue(cles_count_data > 0)

        # Create a CLE with selectable_for_assessment=False
        unselectable_cle = ControlListEntriesFactory(rating="rating123", text="text", selectable_for_assessment=False)

        # Assert that the object was created successfully
        self.assertFalse(unselectable_cle.selectable_for_assessment)
        self.assertTrue(
            ControlListEntry.objects.filter(rating="rating123", selectable_for_assessment=False).count() == 1
        )

        updated_cles_count_model = ControlListEntry.objects.all().count()

        # Assert that the count returned by the db manager has increased by 1
        self.assertTrue(updated_cles_count_model == cles_count_model + 1)

        response = self.client.get(url, **self.exporter_headers)
        updated_cles_data = response.json()
        updated_cles_count_data = len(updated_cles_data)

        # Assert that the count returned by the view has increased by 1
        self.assertTrue(updated_cles_count_data == cles_count_data + 1)

        # Assert that the data returned by the view contains the unselectable CLE
        self.assertIn("rating123", [cle["rating"] for cle in updated_cles_data])
