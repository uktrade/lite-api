from django.urls import reverse
from rest_framework import status

from cases.models import CaseAssignment
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class EndUserAdvisoryUpdate(DataTestClient):
    def setUp(self):
        super().setUp()
        self.end_user_advisory = self.create_end_user_advisory_case(
            "end_user_advisory", "my reasons", organisation=self.organisation
        )
        self.url = reverse("queries:end_user_advisories:end_user_advisory", kwargs={"pk": self.end_user_advisory.id},)

    def test_update_end_user_advisory_status_to_withdrawn_success(self):
        """
        When a case is set to a the withdrawn status, its assigned users, case officer and queues should be removed
        """
        self.end_user_advisory.case_officer = self.gov_user
        self.end_user_advisory.save()
        self.end_user_advisory.queues.set([self.queue])
        case_assignment = CaseAssignment.objects.create(case=self.end_user_advisory, queue=self.queue)
        case_assignment.users.set([self.gov_user])
        data = {"status": CaseStatusEnum.WITHDRAWN}

        response = self.client.put(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.end_user_advisory.refresh_from_db()
        self.assertEqual(self.end_user_advisory.status.status, CaseStatusEnum.WITHDRAWN)
        self.assertEqual(self.end_user_advisory.queues.count(), 0)
        self.assertEqual(self.end_user_advisory.case_officer, None)
        self.assertEqual(CaseAssignment.objects.filter(case=self.end_user_advisory).count(), 0)
