from rest_framework.reverse import reverse

from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.control_list_entries.factories import ControlListEntriesFactory
from test_helpers.clients import DataTestClient


class ControlListEntriesListTests(DataTestClient):
    """
    Most other view tests are in api/staticdata/control_list_entries/test.py
    """

    def setUp(self):
        super().setUp()
        self.url = reverse("staticdata:control_list_entries:control_list_entries")

    def test_gov_user_control_list_entries_list_includes_unselectable_cles(self):
        url = reverse("staticdata:control_list_entries:control_list_entries")
        cles_count_model = ControlListEntry.objects.all().count()

        # Assert that we have at least 1 CLE returned by the db manager
        self.assertTrue(cles_count_model > 0)

        response = self.client.get(url, **self.gov_headers)
        cles_data = response.json().get("control_list_entries")
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

        response = self.client.get(url, **self.gov_headers)
        updated_cles_data = response.json().get("control_list_entries")
        updated_cles_count_data = len(updated_cles_data)

        # Assert that the count returned by the view has increased by 1
        self.assertTrue(updated_cles_count_data == cles_count_data + 1)

        # Assert that the data returned by the view contains the unselectable CLE
        self.assertIn("rating123", [cle["rating"] for cle in updated_cles_data])
