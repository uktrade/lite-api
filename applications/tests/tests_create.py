from django.urls import reverse
from rest_framework import status

from applications.models import Application
from drafts.models import GoodOnDraft
from queues.models import Queue
from static.units.enums import Units
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ApplicationsTests(DataTestClient):

    url = reverse('applications:applications')

    def test_create_application_case_and_addition_to_queue(self):
        """
        Test whether we can create a draft first and then submit it as an application
        """
        draft = OrgAndUserHelper.create_draft_with_good_end_user_site_and_end_user_document(name='test',
                                                                          org=self.test_helper.organisation)

        self.assertEqual(Queue.objects.get(pk='00000000-0000-0000-0000-000000000001').cases.count(), 0)

        data = {'id': draft.id}
        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        application = Application.objects.get(pk=draft.id)

        self.assertEqual(Queue.objects.get(pk='00000000-0000-0000-0000-000000000001').cases.count(), 1)
        self.assertEqual(application.end_user, draft.end_user)

    def test_create_application_with_invalid_id(self):
        """
        Ensure we cannot create a new application object with an invalid draft id.
        """
        draft_id = '90D6C724-0339-425A-99D2-9D2B8E864EC7'

        OrgAndUserHelper.complete_draft(name='test', org=self.test_helper.organisation)

        data = {'id': draft_id}
        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_that_cannot_submit_with_no_sites_or_external(self):
        draft = OrgAndUserHelper.complete_draft('test', self.test_helper.organisation)
        unit1 = Units.NAR
        good = OrgAndUserHelper.create_controlled_good('test good', self.test_helper.organisation)
        good_on_draft_1 = GoodOnDraft(draft=draft, good=good, quantity=20, unit=unit1, value=400)
        good_on_draft_1.save()

        url = reverse('applications:applications')
        data = {'id': draft.id}
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # if POST - end user with no document - 400
    def test_status_code_post_no_end_user_document(self):
        # assemble
        draft = OrgAndUserHelper.create_draft_with_good_end_user_and_site('test', self.test_helper.organisation)
        url = reverse('applications:applications')
        data = {'id': draft.id}

        # act
        response = self.client.post(url, data, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
