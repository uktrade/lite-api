from uuid import UUID

from django.urls import reverse
from rest_framework import status

from applications.models import GoodOnApplication
from goodstype.models import GoodsType
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
        self.assertIsNone(response_data[0]['status'])

    def test_view_hmrc_queries(self):
        """
        Ensure we can get a list of HMRC queries.
        """
        hmrc_query = self.create_hmrc_query(organisation=self.organisation)

        response = self.client.get(self.url, **self.hmrc_exporter_headers)
        response_data = response.json()['results']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['name'], hmrc_query.name)
        self.assertEqual(response_data[0]['application_type']['key'], hmrc_query.application_type)
        self.assertEqual(response_data[0]['organisation']['name'], hmrc_query.organisation.name)
        self.assertIsNone(response_data[0]['export_type'])
        self.assertIsNotNone(response_data[0]['created_at'])
        self.assertIsNotNone(response_data[0]['last_modified_at'])
        self.assertIsNone(response_data[0]['submitted_at'])
        self.assertIsNone(response_data[0]['status'])

    def test_view_draft_standard_application(self):
        """
        Ensure we can view an individual draft.
        """
        standard_application = self.create_standard_application(self.organisation)

        url = reverse('applications:application', kwargs={'pk': standard_application.id}) + '?submitted=false'

        response = self.client.get(url, **self.exporter_headers)

        retrieved_application = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved_application['name'], standard_application.name)
        self.assertEqual(retrieved_application['application_type']['key'], standard_application.application_type)
        self.assertEqual(retrieved_application['export_type']['key'], standard_application.export_type)
        self.assertIsNotNone(retrieved_application['created_at'])
        self.assertIsNotNone(retrieved_application['last_modified_at'])
        self.assertIsNone(retrieved_application['submitted_at'])
        self.assertIsNone(retrieved_application['status'])
        self.assertIsNotNone(GoodOnApplication.objects.get(application__id=standard_application.id))
        self.assertEqual(retrieved_application['end_user']['id'], str(standard_application.end_user.id))
        self.assertEqual(retrieved_application['consignee']['id'], str(standard_application.consignee.id))
        self.assertEqual(retrieved_application['third_parties'][0]['id'],
                         str(standard_application.third_parties.get().id))

    def test_view_draft_hmrc_query(self):
        """
        Ensure we can view an individual draft.
        """
        hmrc_query = self.create_hmrc_query(self.organisation)

        url = reverse('applications:application', kwargs={'pk': hmrc_query.id}) + '?submitted=false'

        response = self.client.get(url, **self.hmrc_exporter_headers)

        retrieved_application = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved_application['name'], hmrc_query.name)
        self.assertEqual(retrieved_application['application_type']['key'], hmrc_query.application_type)
        self.assertIsNotNone(retrieved_application['created_at'])
        self.assertIsNotNone(retrieved_application['last_modified_at'])
        self.assertIsNone(retrieved_application['submitted_at'])
        self.assertIsNone(retrieved_application['status'])
        self.assertEqual(retrieved_application['organisation']['id'], str(hmrc_query.organisation.id))
        self.assertEqual(retrieved_application['hmrc_organisation']['id'], str(hmrc_query.hmrc_organisation.id))
        self.assertIsNotNone(GoodsType.objects.get(application__id=hmrc_query.id))
        self.assertEqual(retrieved_application['end_user']['id'], str(hmrc_query.end_user.id))
        self.assertEqual(retrieved_application['consignee']['id'], str(hmrc_query.consignee.id))
        self.assertEqual(retrieved_application['third_parties'][0]['id'], str(hmrc_query.third_parties.get().id))

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
