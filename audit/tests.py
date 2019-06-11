from django.urls import reverse

from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class AuditTests(DataTestClient):

    url = reverse('audit:audit_detail')

    def test_create_application_case_and_addition_to_queue(self):
        """
        Test whether we can create a draft first and then submit it as an application
        """
        draft = OrgAndUserHelper.create_draft_with_good_end_user_and_site(name='test',
                                                                          org=self.test_helper.organisation)
        application = OrgAndUserHelper.submit_draft(self, draft)

        response = self.client.get(self.url)

        print(response.json())
