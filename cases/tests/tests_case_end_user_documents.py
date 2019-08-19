from django.urls import reverse

from cases.models import Case
from test_helpers.clients import DataTestClient


class CaseEndUserDocumentTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.file_name = 'file343.pdf'
        self.safe = True

        self.draft = self.test_helper.create_draft_with_good_end_user_and_site(
            'Example Application 854957', self.test_helper.organisation)
        self.test_helper.create_custom_document_for_end_user(end_user=self.draft.end_user,
                                                             name=self.file_name,
                                                             safe=self.safe)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.case = Case.objects.get(application=self.application)

    def test_case_contains_end_user_document(self):
        # act
        response = self.client.get(reverse('cases:case', kwargs={'pk': self.case.id}), **self.gov_headers)

        # assert
        data = response.json()

        self.assertIsNotNone(data['case']['application']['destinations']['data']['document'])
        self.assertEquals(self.file_name,
                          data['case']['application']['destinations']['data']['document']['name'])
        self.assertEquals(self.safe,
                          data['case']['application']['destinations']['data']['document']['safe'])
