from django.urls import path, include
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

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
        self.org = self.test_helper.organisation

    # def test_that_endusers_are_added_to_application_when_submitted(self):
    #     draft = OrgAndUserHelper.complete_draft('test', self.test_helper.organisation)
    #     site2, address = OrgAndUserHelper.create_site('site2', self.test_helper.organisation)
    #     end_user1 = OrgAndUserHelper.create_end_user('test_end_user', self.org)
    #     end_user2 = OrgAndUserHelper.create_end_user('test_end_user2', self.org)
    #     unit1 = Units.NAR
    #     good = OrgAndUserHelper.create_controlled_good('test good', self.test_helper.organisation)
    #     good_on_draft_1 = GoodOnDraft(draft=draft, good=good, quantity=20, unit=unit1, value=400)
    #     good_on_draft_1.save()
    #     site_on_draft_1 = SiteOnDraft(site=self.test_helper.primary_site, draft=draft)
    #     site_on_draft_2 = SiteOnDraft(site=site2, draft=draft)
    #     site_on_draft_1.save()
    #     site_on_draft_2.save()
    #     enduser_on_draft1 = EndUserOnDraft(end_user=end_user1, draft=draft)
    #     enduser_on_draft2 = EndUserOnDraft(end_user=end_user2, draft=draft)
    #     enduser_on_draft1.save()
    #     enduser_on_draft2.save()
    #
    #     url = reverse('applications:applications')
    #     data = {'id': draft.id}
    #     response = self.client.post(url, data, format='json', **self.headers)
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(SiteOnApplication.objects.count(), 2)
    #     self.assertEqual(EndUserOnApplication.objects.count(), 2)
    #     application = Application.objects.get()
    #     self.assertEqual(SiteOnApplication.objects.filter(application=application).count(), 2)
