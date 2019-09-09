from uuid import UUID

from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class DraftTests(DataTestClient):

    url = reverse('drafts:drafts')

    def test_view_drafts(self):
        """
        Ensure we can get a list of drafts.
        """
        self.create_standard_draft(self.organisation)

        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['drafts']), 1)

    def test_view_draft(self):
        """
        Ensure we can view an individual draft.
        """
        draft = self.create_standard_draft(self.organisation)

        url = reverse('drafts:draft', kwargs={'pk': draft.id})

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_incorrect_draft(self):
        """
        Ensure we cannot get a draft if the id is incorrect.
        """
        invalid_id = UUID('90D6C724-0339-425A-99D2-9D2B8E864EC6')

        url = reverse('drafts:draft', kwargs={'pk': invalid_id})
        response = self.client.put(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_only_sees_their_organisations_drafts_in_list(self):
        organisation_2 = self.create_organisation()
        self.create_standard_draft(organisation_2)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['drafts']), 0)

    def test_user_cannot_see_details_of_another_organisations_draft(self):
        organisation_2 = self.create_organisation()
        draft = self.create_standard_draft(organisation_2)

        url = reverse('drafts:draft', kwargs={'pk': draft.id})

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
