from api.cases.models import Advice
from api.cases.enums import AdviceType
from api.cases.tests.factories import UserAdviceFactory
from api.users.tests.factories import GovUserFactory
from test_helpers.clients import DataTestClient

from django.urls import reverse


class DeleteUserAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.application)
        self.gov_user_2 = GovUserFactory(baseuser_ptr__email="user@email.com", team=self.team)
        self.good = self.case.goods.first().good
        self.end_user = self.case.end_user
        self.standard_case_url = reverse("cases:user_advice", kwargs={"pk": self.case.id})

    def test_delete_current_user_advice(self):
        UserAdviceFactory(user=self.gov_user, case=self.case, type=AdviceType.APPROVE, good=self.good)
        UserAdviceFactory(user=self.gov_user, case=self.case, type=AdviceType.PROVISO, end_user=self.end_user.party)
        UserAdviceFactory(user=self.gov_user_2, case=self.case, type=AdviceType.REFUSE, good=self.good)

        resp = self.client.delete(self.standard_case_url, **self.gov_headers)

        self.assertEqual(resp.status_code, 200)
        remaining_records = Advice.objects.all()
        self.assertEqual(remaining_records.count(), 1)
        self.assertEqual(remaining_records[0].user, self.gov_user_2)

    def test_creates_audit_trail(self):
        UserAdviceFactory(user=self.gov_user, case=self.case, type=AdviceType.APPROVE, end_user=self.end_user.party)

        self.client.delete(self.standard_case_url, **self.gov_headers)

        response = self.client.get(reverse("cases:activity", kwargs={"pk": self.application.id}), **self.gov_headers)
        audit_entries = response.json()["activity"]
        self.assertEqual(len(audit_entries), 2)  # one entry for case creation, one entry for advice deletion
        self.assertEqual(len([a for a in audit_entries if a["text"] == "cleared their recommendation."]), 1)
