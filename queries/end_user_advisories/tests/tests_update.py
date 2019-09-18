from rest_framework import status
from rest_framework.reverse import reverse


from static.statuses.enums import CaseStatusEnum
from picklists.enums import PickListStatus, PicklistType
from test_helpers.clients import DataTestClient


class EndUserAdvisoryUpdate(DataTestClient):

    def setUp(self):
        super().setUp()
        self.end_user_advisory_case, self.end_user_advisory = self.create_end_user_advisory_case('end_user_advisory', "my reasons", organisation=self.organisation)
        self.url = reverse('queries:end_user_advisories:end_user_advisory', kwargs={'pk': self.end_user_advisory.id})

    def test_update_end_user_advisory_status(self):
        data = {
            'status': CaseStatusEnum.MORE_INFORMATION_REQUIRED
        }

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
