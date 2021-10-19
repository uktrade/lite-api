from api.cases.models import Advice
from api.cases.enums import AdviceLevel, AdviceType
from api.users.tests.factories import GovUserFactory
from test_helpers.clients import DataTestClient

from django.urls import reverse


class DeleteUserAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.application)
        self.gov_user_2 = GovUserFactory(baseuser_ptr__email="user@email.com", team=self.team)

        self.standard_case_url = reverse("cases:user_advice", kwargs={"pk": self.case.id})

    def test_delete_current_user_advice(self):
        self.create_advice(self.gov_user, self.application, "end_user", AdviceType.APPROVE, AdviceLevel.USER)
        self.create_advice(self.gov_user_2, self.application, "good", AdviceType.REFUSE, AdviceLevel.USER)
        self.create_advice(self.gov_user, self.application, "good", AdviceType.PROVISO, AdviceLevel.USER)

        resp = self.client.delete(self.standard_case_url, **self.gov_headers)

        self.assertEqual(resp.status_code, 200)
        remaining_records = Advice.objects.all()
        self.assertEqual(remaining_records.count(), 1)
        self.assertEqual(remaining_records[0].user, self.gov_user_2)

    def test_creates_audit_trail(self):
        self.create_advice(self.gov_user, self.application, "end_user", AdviceType.APPROVE, AdviceLevel.USER)

        self.client.delete(self.standard_case_url, **self.gov_headers)

        response = self.client.get(reverse("cases:activity", kwargs={"pk": self.application.id}), **self.gov_headers)
        audit_entries = response.json()["activity"]
        self.assertEqual(len(audit_entries), 2)  # one entry for case creation, one entry for advice deletion
        self.assertEqual(len([a for a in audit_entries if a["text"] == "cleared user advice."]), 1)
