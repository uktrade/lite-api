from django.urls import reverse

from cases.models import Case
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class CaseEndUserDocumentTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.draft = self.test_helper.create_draft_with_good_end_user_site_and_end_user_document(
            'Example Application 854957', self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.case = Case.objects.get(application=self.application)


    def test_case_contains_end_user_document(self):
        print('THIS TEST')

        response = self.client.get(reverse('cases:case', kwargs={'pk': self.case.id}), **self.gov_headers)
        data = response.json()

        print('DATA', data)

        #TODO: Assert data contains end user document