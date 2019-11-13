from uuid import UUID

from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class DraftTests(DataTestClient):

    url = reverse("applications:applications") + "?submitted=false"

    def test_view_drafts(self):
        """
        Ensure we can get a list of drafts.
        """
        self.create_standard_application(self.organisation)

        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["applications"]), 1)

    def test_view_draft(self):
        """
        Ensure we can view an individual draft.
        """
        draft = self.create_standard_application(self.organisation)

        url = (
            reverse("applications:application", kwargs={"pk": draft.id})
            + "?submitted=false"
        )

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_incorrect_draft(self):
        """
        Ensure we cannot get a draft if the id is incorrect.
        """
        invalid_id = UUID("90D6C724-0339-425A-99D2-9D2B8E864EC6")

        url = (
            reverse("applications:application", kwargs={"pk": invalid_id})
            + "?submitted=false"
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_only_sees_their_organisations_drafts_in_list(self):
        organisation_2 = self.create_organisation_with_exporter_user()
        self.create_standard_application(organisation_2)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["applications"]), 0)

    def test_user_cannot_see_details_of_another_organisations_draft(self):
        organisation_2 = self.create_organisation_with_exporter_user()
        draft = self.create_standard_application(organisation_2)

        url = (
            reverse("applications:application", kwargs={"pk": draft.id})
            + "?submitted=false"
        )

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
