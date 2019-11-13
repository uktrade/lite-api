from rest_framework import status
from rest_framework.reverse import reverse

from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from static.statuses.libraries.get_case_status import get_case_status_by_status


class EndUserAdvisoryUpdate(DataTestClient):
    def setUp(self):
        super().setUp()
        self.end_user_advisory = self.create_end_user_advisory_case(
            "end_user_advisory", "my reasons", organisation=self.organisation
        )
        self.url = reverse(
            "queries:end_user_advisories:end_user_advisory",
            kwargs={"pk": self.end_user_advisory.id},
        )

    def test_update_end_user_advisory_status(self):
        data = {"status": CaseStatusEnum.INITIAL_CHECKS}

        response = self.client.put(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_end_user_advisory = EndUserAdvisoryQuery.objects.get(
            pk=self.end_user_advisory.id
        )
        casestatus = get_case_status_by_status(CaseStatusEnum.INITIAL_CHECKS)
        self.assertEqual(new_end_user_advisory.status, casestatus)
