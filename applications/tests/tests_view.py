from uuid import UUID

from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class DraftTests(DataTestClient):

    url = reverse('applications:applications') + '?submitted=false'

    def test_view_drafts(self):
        """
        Ensure we can get a list of drafts.
        """
        standard_application = self.create_standard_application(self.organisation)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()['results']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['name'], standard_application.name)
        self.assertEqual(response_data[0]['application_type']['key'], standard_application.application_type)
        self.assertEqual(response_data[0]['export_type']['key'], standard_application.export_type)
        self.assertIsNotNone(response_data[0]['created_at'])
        self.assertIsNotNone(response_data[0]['last_modified_at'])
        self.assertIsNone(response_data[0]['submitted_at'])
        self.assertEqual(response_data[0]['status']['key'], standard_application.status)

    def test_view_hmrc_queries(self):
        """
        Ensure we can get a list of HMRC queries.
        """
        hmrc_query = self.create_hmrc_query(organisation=self.organisation,
                                            hmrc_organisation=self.hmrc_organisation)

        response = self.client.get(self.url, **self.hmrc_exporter_headers)
        response_data = response.json()['results']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['name'], hmrc_query.name)
        self.assertEqual(response_data[0]['application_type']['key'], hmrc_query.application_type)
        self.assertIsNone(response_data[0]['export_type'])
        self.assertIsNotNone(response_data[0]['created_at'])
        self.assertIsNotNone(response_data[0]['last_modified_at'])
        self.assertIsNone(response_data[0]['submitted_at'])
        self.assertEqual(response_data[0]['status']['key'], hmrc_query.status)

    def test_view_draft(self):
        """
        Ensure we can view an individual draft.
        """
        draft = self.create_standard_application(self.organisation)

        url = reverse('applications:application', kwargs={'pk': draft.id}) + '?submitted=false'

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_incorrect_draft(self):
        """
        Ensure we cannot get a draft if the id is incorrect.
        """
        invalid_id = UUID('90D6C724-0339-425A-99D2-9D2B8E864EC6')

        url = reverse('applications:application', kwargs={'pk': invalid_id}) + '?submitted=false'
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_only_sees_their_organisations_drafts_in_list(self):
        organisation_2, _ = self.create_organisation_with_exporter_user()
        self.create_standard_application(organisation_2)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['results']), 0)

    def test_user_cannot_see_details_of_another_organisations_draft(self):
        organisation_2, _ = self.create_organisation_with_exporter_user()
        draft = self.create_standard_application(organisation_2)

        url = reverse('applications:application', kwargs={'pk': draft.id}) + '?submitted=false'

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
