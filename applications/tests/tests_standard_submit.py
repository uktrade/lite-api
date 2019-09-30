from django.urls import reverse
from rest_framework import status

from cases.models import Case
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class ApplicationsTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_draft(self.organisation)
        self.url = reverse('applications:application_submit', kwargs={'pk': self.draft.id})

    def test_successful_standard_submit(self):
        """
        Test whether we can submit a standard application
        """

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get()
        self.assertEqual(case.application.id, self.draft.id)
        self.assertIsNotNone(case.application.submitted_at)
        self.assertEqual(case.application.status.status, CaseStatusEnum.SUBMITTED)

    def test_create_application_with_invalid_id(self):
        """
        Ensure we cannot create a new application object with an invalid draft id.
        """
        draft_id = '90D6C724-0339-425A-99D2-9D2B8E864EC7'
        url = 'applications/' + draft_id + '/submit/'

        response = self.client.put(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_that_cannot_submit_with_no_sites_or_external(self):
        """
        Ensure we cannot create a new application without a site
        """
        draft = self.create_standard_draft_without_site(self.organisation)
        url = reverse('applications:application_submit', kwargs={'pk': draft.id})

        response = self.client.put(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_code_post_no_end_user_document(self):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user doesn't have a document attached
        When an application is submitted
        Then a 400 BAD REQUEST is returned
        """
        # assemble
        draft = self.create_standard_draft_without_end_user_document(self.organisation)
        url = reverse('applications:application_submit', kwargs={'pk': draft.id})

        # act
        response = self.client.put(url, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_code_post_with_untested_document(self):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user has a document attached
        And the end user document has not been scanned by an AV
        When an application is submitted
        Then a 400 BAD REQUEST is returned
        And the response contains a message saying that the document is still being processed
        """
        # assemble
        draft = self.create_standard_draft_without_end_user_document(self.organisation, 'test')
        self.create_document_for_party(party=draft.end_user, name='blah', safe=None)
        url = reverse('applications:application_submit', kwargs={'pk': draft.id})

        # act
        response = self.client.put(url, **self.exporter_headers)

        # assert
        self.assertContains(response, text='still being processed', status_code=status.HTTP_400_BAD_REQUEST)

    def test_status_code_post_with_infected_document(self):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user has a document attached
        And the AV marked the document as unsafe
        When an application is submitted
        Then a 400 BAD REQUEST is returned
        And the response contains a message saying that the document is infected
        """
        # assemble
        draft = self.create_standard_draft_without_end_user_document(self.organisation, 'test')
        self.create_document_for_party(party=draft.end_user, name='blah', safe=False)
        url = reverse('applications:application_submit', kwargs={'pk': draft.id})

        # act
        response = self.client.put(url, **self.exporter_headers)

        # assert
        self.assertContains(response, text='infected end user document', status_code=status.HTTP_400_BAD_REQUEST)
