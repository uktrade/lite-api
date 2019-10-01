from django.urls import reverse
from rest_framework import status

from applications.models import GoodOnApplication
from cases.models import Case
from content_strings.strings import get_string
from goods.models import Good
from parties.document.models import PartyDocument
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class ApplicationsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_draft(self.organisation)
        self.url = reverse('applications:application_submit', kwargs={'pk': self.draft.id})

    def test_successful_standard_submit(self):
        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get()
        self.assertEqual(case.application.id, self.draft.id)
        self.assertIsNotNone(case.application.submitted_at)
        self.assertEqual(case.application.status.status, CaseStatusEnum.SUBMITTED)

    def test_create_application_with_invalid_id(self):
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
        draft = self.create_standard_draft_without_end_user(self.organisation)
        draft.end_user = self.create_end_user('End User', self.organisation)
        draft.save()
        url = reverse('applications:application_submit', kwargs={'pk': draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_code_post_with_untested_document(self):
        draft = self.create_standard_draft(self.organisation, safe_document=None)
        url = reverse('applications:application_submit', kwargs={'pk': draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(response, text='still being processed', status_code=status.HTTP_400_BAD_REQUEST)

    def test_status_code_post_with_infected_document(self):
        draft = self.create_standard_draft(self.organisation, safe_document=False)
        url = reverse('applications:application_submit', kwargs={'pk': draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(response, text='infected end user document', status_code=status.HTTP_400_BAD_REQUEST)

    def test_submit_draft_with_no_ultimate_end_users_unsuccessful(self):
        """
        This should be unsuccessful as an ultimate end user is required when
        there is a part which is to be incorporated into another good
        """
        draft = self.create_standard_draft_without_ultimate_user(self.organisation)

        self.draft = self.create_standard_draft(self.organisation)

        part_good = Good(is_good_end_product=False,
                         is_good_controlled=True,
                         control_code='ML17',
                         organisation=self.organisation,
                         description='a good',
                         part_number='123456')
        part_good.save()

        GoodOnApplication(good=part_good,
                          application=self.draft,
                          quantity=17,
                          value=18).save()

        url = reverse('applications:application_submit', kwargs={'pk': draft.id})

        response = self.client.put(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data, {
            'errors': {'ultimate_end_users': get_string('applications.standard.no_ultimate_end_users_set')}})
