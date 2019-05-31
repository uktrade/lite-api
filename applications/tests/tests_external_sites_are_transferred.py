from django.urls import path, include, reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from applications.models import Application, ExternalSiteOnApplication, SiteOnApplication
from drafts.models import GoodOnDraft, ExternalSiteOnDraft
from static.units.units import Units
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ApplicationsTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient()

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_that_external_sites_are_added_to_application_when_submitted(self):
        draft = OrgAndUserHelper.complete_draft('test', self.test_helper.organisation)
        site1 = OrgAndUserHelper.create_external_site('site1', self.test_helper.organisation)
        site2 = OrgAndUserHelper.create_external_site('site2', self.test_helper.organisation)
        unit1 = Units.NAR
        good = OrgAndUserHelper.create_controlled_good('test good', self.test_helper.organisation)
        GoodOnDraft(draft=draft, good=good, quantity=20, unit=unit1, value=400).save()
        ExternalSiteOnDraft(external_site=site1, draft=draft).save()
        ExternalSiteOnDraft(external_site=site2, draft=draft).save()
        draft.end_user = OrgAndUserHelper.create_end_user('test', self.test_helper.organisation)
        draft.activity = 'Brokering'
        draft.save()

        url = reverse('applications:applications')
        data = {'id': draft.id}
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExternalSiteOnApplication.objects.count(), 2)
        application = Application.objects.get()
        self.assertEqual(ExternalSiteOnApplication.objects.filter(application=application).count(), 2)
        self.assertEqual(SiteOnApplication.objects.filter(application=application).count(), 0)
