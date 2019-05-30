from django.urls import reverse
from rest_framework import status

from applications.models import Application, GoodOnApplication
from test_helpers.clients import DataTestClient
from drafts.models import GoodOnDraft, SiteOnDraft
from test_helpers.org_and_user_helper import OrgAndUserHelper
from static.units.units import Units


class ApplicationsTests(DataTestClient):

    url = reverse('applications:applications')

    def test_that_goods_are_added_to_application_when_submitted(self):
        draft = OrgAndUserHelper.complete_draft('test', self.test_helper.organisation)
        good = OrgAndUserHelper.create_controlled_good('test good', self.test_helper.organisation)
        SiteOnDraft(site=self.test_helper.primary_site, draft=draft).save()

        GoodOnDraft(draft=draft, good=good, quantity=20, unit=Units.NAR, value=400).save()
        GoodOnDraft(draft=draft, good=good, quantity=90, unit=Units.KGM, value=500).save()
        draft.end_user = OrgAndUserHelper.create_end_user('test', self.test_helper.organisation)
        draft.save()
        data = {'id': draft.id}
        response = self.client.post(self.url, data,**self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GoodOnApplication.objects.count(), 2)
        application = Application.objects.get()
        self.assertEqual(GoodOnApplication.objects.filter(application=application).count(), 2)

    def test_that_cannot_submit_with_no_goods(self):
        draft = OrgAndUserHelper.complete_draft('test', self.test_helper.organisation)
        site_on_draft_1 = SiteOnDraft(site=self.test_helper.primary_site, draft=draft)
        site_on_draft_1.save()

        url = reverse('applications:applications')
        data = {'id': draft.id}
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
