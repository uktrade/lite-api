from django.urls import reverse
from rest_framework import status

from applications.models import Application
from cases.models import Case
from drafts.models import SiteOnDraft, GoodOnDraft
from quantity.units import Units
from queues.models import Queue
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ApplicationsTests(DataTestClient):

    url = reverse('applications:applications')

    def test_create_application_case_and_addition_to_queue(self):
        """
        Test whether we can create a draft first and then submit it as an application
        """

        draft = OrgAndUserHelper.complete_draft(name='test', org=self.test_helper.organisation)
        draft_id = draft.id
        site_on_draft_1 = SiteOnDraft(site=self.test_helper.primary_site, draft=draft)
        site_on_draft_1.save()
        good = OrgAndUserHelper.create_controlled_good('test good', self.test_helper.organisation)
        good_on_draft_1 = GoodOnDraft(draft=draft, good=good, quantity=20, unit=Units.NAR, value=400)
        good_on_draft_1.save()
        self.assertEqual(Queue.objects.get(pk='00000000-0000-0000-0000-000000000001').cases.count(), 0)

        data = {'id': draft_id}
        response = self.client.post(self.url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Case.objects.get(application=Application.objects.get(pk=draft_id)).application,
                         Application.objects.get(pk=draft_id))
        self.assertEqual(Queue.objects.get(pk='00000000-0000-0000-0000-000000000001').cases.count(), 1)

    def test_create_application_with_invalid_id(self):
        """
        Ensure we cannot create a new application object with an invalid draft id.
        """
        draft_id = '90D6C724-0339-425A-99D2-9D2B8E864EC7'

        OrgAndUserHelper.complete_draft(name='test', org=self.test_helper.organisation)

        data = {'id': draft_id}
        response = self.client.post(self.url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
