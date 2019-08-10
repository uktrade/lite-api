from django.urls import reverse
from rest_framework import status

from applications.models import Application, SiteOnApplication, ExternalLocationOnApplication
from drafts.models import GoodOnDraft, SiteOnDraft
from static.units.enums import Units
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ApplicationsTests(DataTestClient):

    def test_that_sites_are_added_to_application_when_submitted(self):
        draft = OrgAndUserHelper.complete_draft('test', self.test_helper.organisation)
        site2, address = self.create_site('site2', self.test_helper.organisation)
        unit1 = Units.NAR
        good = self.create_controlled_good('test good', self.test_helper.organisation)
        GoodOnDraft(draft=draft, good=good, quantity=20, unit=unit1, value=400).save()
        SiteOnDraft(site=self.test_helper.primary_site, draft=draft).save()
        SiteOnDraft(site=site2, draft=draft).save()
        draft.end_user = self.create_end_user('test', self.test_helper.organisation)
        draft.save()

        url = reverse('applications:applications')
        data = {'id': draft.id}
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SiteOnApplication.objects.count(), 2)
        application = Application.objects.get()
        self.assertEqual(SiteOnApplication.objects.filter(application=application).count(), 2)
        self.assertEqual(ExternalLocationOnApplication.objects.filter(application=application).count(), 0)
