from django.urls import reverse

from cases.models import Case
from test_helpers.clients import DataTestClient


class CaseEndUserDocumentTests(DataTestClient):
    def setUp(self):
        super().setUp()

    def test_case_contains_end_user_document(self):
        # assemble
        draft = self.create_standard_draft_without_end_user_document(self.exporter_user.organisation,
                                                                     'Example Application 854957')
        self.create_document_for_end_user(end_user=draft.end_user,
                                          name='file343.pdf',
                                          safe=True)
        application = self.submit_draft(draft)
        case = Case.objects.get(application=application)

        # act
        response = self.client.get(reverse('cases:case', kwargs={'pk': case.id}), **self.gov_headers)

        # assert
        data = response.json()

        self.assertIsNotNone(data['case']['application']['destinations']['data']['document'])
        self.assertEquals('file343.pdf',
                          data['case']['application']['destinations']['data']['document']['name'])
        self.assertEquals(True,
                          data['case']['application']['destinations']['data']['document']['safe'])
